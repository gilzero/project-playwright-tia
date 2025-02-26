# app/scraper.py
import time
import re
import random
from typing import List, Optional, Dict, Any
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from random import uniform, choice
from app.models import Article, ScraperConfig
from app.utils import setup_output_directory, save_articles_to_csv, save_articles_to_json
from app.human_behavior import HumanBehaviorSimulator
from app.logger import get_logger, log_exception, log_summary
from tqdm import tqdm
from playwright.async_api import Error as PlaywrightError
from datetime import datetime
import asyncio
import json
import os
from dateutil import parser

# Get the logger instance
logger = get_logger()

class TechInAsiaScraper:
    def __init__(self, config: ScraperConfig):
        """Initialize the scraper with configuration"""
        self.config = config
        self.browser = None
        self.page = None
        self.human_simulator = None
        setup_output_directory(self.config.output_dir)
        self.processed_article_ids = set()
        self.incomplete_articles = 0
        self.total_articles = 0
        self.articles_data = []
        logger.info(f"Initialized TechInAsiaScraper with category: {self.config.category}")
        logger.debug(f"Scraper configuration: {self.config.model_dump_json()}")

    async def setup_browser(self, playwright):
        """Initialize Playwright browser and page with randomized settings"""
        try:
            logger.info("Setting up browser...")
            self.browser = await playwright.chromium.launch(headless=True)
            
            # Select random user agent and viewport if randomization is enabled
            context_options = {}
            
            if self.config.randomize_user_agent:
                user_agent = random.choice(self.config.user_agents)
                context_options["user_agent"] = user_agent
                logger.info(f"🔄 Using random user agent: {user_agent[:30]}...")
            
            if self.config.randomize_viewport:
                viewport = random.choice(self.config.viewport_sizes)
                context_options["viewport"] = viewport
                logger.info(f"🔄 Using random viewport: {viewport}")
            
            # Create a new browser context with the selected options
            context = await self.browser.new_context(**context_options)
            self.page = await context.new_page()
            
            # Initialize human behavior simulator
            self.human_simulator = HumanBehaviorSimulator(self.page, self.config)
            
            logger.info("🚀 Playwright browser initialized successfully")
        except PlaywrightError as e:
            log_exception(
                logger,
                e,
                "Playwright error during browser initialization",
                {"config": self.config.model_dump()}
            )
            raise
        except Exception as e:
            log_exception(
                logger,
                e,
                "Unexpected error during browser initialization",
                {"config": self.config.model_dump()}
            )
            raise

    async def navigate_to_url(self, url: str) -> bool:
        """Navigate to a URL with retry mechanism"""
        for attempt in range(self.config.retry_count):
            try:
                logger.info(f"🌐 Navigating to URL: {url} (Attempt {attempt + 1}/{self.config.retry_count})")
                await self.page.goto(url, timeout=self.config.timeout)
                logger.info("Page loaded successfully.")
                return True
            except PlaywrightTimeoutError:
                logger.warning(f"⚠️ Timeout navigating to {url} (Attempt {attempt + 1}/{self.config.retry_count})")
                if attempt < self.config.retry_count - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt + random.uniform(0, 1)
                    logger.info(f"⏱️ Waiting {wait_time:.2f}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    log_exception(
                        logger,
                        PlaywrightTimeoutError(f"Timeout after {self.config.retry_count} attempts"),
                        f"Failed to navigate to {url}",
                        {"url": url, "timeout": self.config.timeout, "retry_count": self.config.retry_count}
                    )
                    return False
            except Exception as e:
                log_exception(
                    logger,
                    e,
                    f"Error navigating to {url}",
                    {"url": url, "attempt": attempt + 1}
                )
                return False
        return False

    def _is_valid_article(self, article: Article) -> bool:
        """Validate if the article has all required fields"""
        if not article.article_url:
            logger.warning(f"⚠️ Skipping article with missing article_url: {article.article_id}")
            return False
        return True

    def _clean_article_data(self, article: Article) -> Article:
        """Clean and normalize article data"""
        return article

    def parse_article(self, article_element) -> Optional[Article]:
        """Parse a single article element"""
        try:
            # Try to find content div with class 'post-content'
            content_div = article_element.find('div', class_='post-content')
            
            # If not found, try to find any div that might contain the content
            if not content_div:
                # Try other common content div classes
                content_div = article_element.find('div', class_=lambda c: c and ('content' in c or 'article' in c))
                
                # If still not found, use the article element itself as the content container
                if not content_div:
                    content_div = article_element
                    logger.debug("Using article element as content container")
                
            article_id, article_url = self._extract_article_id_and_url(content_div)
            if not article_id or not article_url:
                return None

            title = self._extract_title(content_div)
            source, source_url = self._extract_source_info(content_div)
            image_url = self._extract_image_url(article_element)
            posted_time, relative_time = self._extract_time_info(article_element)
            categories, tags = self._extract_categories_and_tags(article_element)

            article = Article(
                article_id=article_id,
                title=title,
                article_url=article_url,
                source=source,
                source_url=source_url,
                image_url=image_url,
                posted_time=posted_time,
                relative_time=relative_time,
                categories=categories,
                tags=tags,
            )
            logger.info(f"🎉 Article parsing complete: {article_id}")
            return article

        except AttributeError as e:
            log_exception(
                logger,
                e,
                "AttributeError parsing article",
                {"article_element": str(article_element)[:100]}
            )
            return None
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error parsing article",
                {"article_element": str(article_element)[:100]}
            )
            return None

    def _extract_article_id_and_url(self, content_div) -> tuple[Optional[str], Optional[str]]:
        """Extract article ID and URL"""
        try:
            # First try to find links with href attributes
            article_links = content_div.find_all('a', href=True)
            
            # If no links found in content_div, try to find links in the parent element
            if not article_links and content_div.parent:
                article_links = content_div.parent.find_all('a', href=True)
                
            # If still no links, try to find links in the entire article element
            if not article_links and hasattr(content_div, 'find_parent'):
                article_element = content_div.find_parent('article')
                if article_element:
                    article_links = article_element.find_all('a', href=True)
            
            if article_links:
                # Get the first link with a non-empty href
                for link in article_links:
                    href = link.get('href')
                    if href and href.strip():
                        article_url = f"https://www.techinasia.com{href}" if not href.startswith('http') else href
                        
                        # Extract article ID from URL
                        match = re.search(r'/([^/]+)$', href)
                        article_id = match.group(1) if match else href.split('/')[-1]
                        
                        # If article_id is empty, use the domain name
                        if not article_id or article_id == '':
                            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', article_url)
                            article_id = domain_match.group(1) if domain_match else None
                        
                        logger.info(f"Parsing article: {article_id}")
                        return article_id, article_url
                
            # If we get here, no suitable links were found
            logger.warning("No article links found.")
            return None, None
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error extracting article ID and URL",
                {"content_div": str(content_div)[:100]}
            )
            return None, None

    def _extract_title(self, content_div) -> Optional[str]:
        """Extract the title of the article"""
        try:
            # Try to find the title in h3 with class post-title
            title_element = content_div.find('h3', class_='post-title')
            
            # If not found, try to find any h3 element
            if not title_element:
                title_element = content_div.find('h3')
                
            # If still not found, try to find the first link's text
            if not title_element:
                links = content_div.find_all('a')
                if links:
                    return links[0].get_text(strip=True)
                    
            return title_element.get_text(strip=True) if title_element else None
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error extracting title",
                {"content_div": str(content_div)[:100]}
            )
            return None

    def _extract_source_info(self, content_div) -> tuple[Optional[str], Optional[str]]:
        """Extract source name and URL"""
        try:
            logger.info(f"  - 📰 Extracting source...")
            
            # Try to find source in span with class post-source-name
            source_element = content_div.find('span', class_='post-source-name')
            
            # If not found, try to find any span that might contain source info
            if not source_element:
                spans = content_div.find_all('span')
                for span in spans:
                    if span.text and len(span.text.strip()) < 30:  # Assuming source name is relatively short
                        source_element = span
                        break
            
            source = source_element.text.strip() if source_element else None
            logger.info(f"  - ✅ Source extracted: {source}")

            # Try to find source URL in a with class post-source
            source_link = content_div.find('a', class_='post-source')
            
            # If not found, try to find the second link (first is usually article link)
            if not source_link:
                links = content_div.find_all('a')
                if len(links) > 1:
                    source_link = links[1]
            
            source_url = source_link.get('href') if source_link else None
            if source_url and not source_url.startswith('http'):
                source_url = f"https://www.techinasia.com{source_url}"
                
            logger.info(f"  - 🌐 Source URL extracted: {source_url}")
            return source, source_url
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error extracting source info",
                {"content_div": str(content_div)[:100]}
            )
            return None, None

    def _extract_image_url(self, article_element) -> Optional[str]:
        """Extract image URL"""
        try:
            # Try to find image in div with class post-image
            image_div = article_element.find('div', class_='post-image')
            
            # If found, look for img tag
            if image_div:
                img_tag = image_div.find('img')
                if img_tag and img_tag.get('src'):
                    return img_tag['src']
            
            # If not found, try to find any img tag in the article
            img_tag = article_element.find('img')
            if img_tag and img_tag.get('src'):
                return img_tag['src']
                
            # If still not found, try to find background-image in style attribute
            elements_with_style = article_element.find_all(lambda tag: tag.has_attr('style') and 'background-image' in tag['style'])
            if elements_with_style:
                style = elements_with_style[0]['style']
                match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error extracting image URL",
                {"article_element": str(article_element)[:100]}
            )
            return None

    def _extract_time_info(self, article_element) -> tuple[Optional[str], Optional[str]]:
        """Extract posted time and relative time"""
        try:
            logger.info(f"  - ⏰ Extracting time info...")
            
            # Try to find time element
            time_element = article_element.find('time')
            
            # If not found, try to find spans that might contain time info
            if not time_element:
                spans = article_element.find_all('span')
                for span in spans:
                    text = span.text.strip()
                    # Look for typical time patterns like "2 hours ago", "yesterday", etc.
                    if re.search(r'(ago|hour|day|week|month|year|yesterday|today)', text, re.IGNORECASE):
                        relative_time = text
                        return None, relative_time
            
            relative_time = time_element.text.strip() if time_element else 'N/A'
            
            posted_time = None
            if time_element and time_element.get('datetime'):
                try:
                    dt = parser.parse(time_element.get('datetime'))
                    posted_time = dt.strftime("%I:%M %p at %b %d, %Y")
                except Exception as e:
                    log_exception(
                        logger,
                        e,
                        "Error parsing datetime",
                        {"datetime_str": time_element.get('datetime')}
                    )
            
            logger.info(f"  - ⏰ Time info extracted: {posted_time} ({relative_time})")
            return posted_time, relative_time
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error extracting time info",
                {"article_element": str(article_element)[:100]}
            )
            return None, 'N/A'

    def _extract_categories_and_tags(self, article_element) -> tuple[List[str], List[str]]:
        """Extract categories and tags"""
        try:
            logger.info(f"  - 🏷️ Extracting categories and tags...")
            categories = []
            tags = []
            
            # Try to extract categories from category-link class
            category_links = article_element.find_all('a', class_='category-link')
            if category_links:
                categories = [link.text.strip() for link in category_links if link.text.strip()]
            
            # If no categories found, try to use the main category from the URL
            if not categories and self.config.category:
                categories = [self.config.category]
            
            # Extract tags (if available)
            tag_links = article_element.find_all('a', class_='tag-link')
            if tag_links:
                tags = [link.text.strip() for link in tag_links if link.text.strip()]
            
            logger.info(f"  - 🏷️ Categories: {categories}, Tags: {tags}")
            return categories, tags
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error extracting categories and tags",
                {"article_element": str(article_element)[:100]}
            )
            return [], []

    async def extract_article_content(self, article: Article) -> Optional[str]:
        """Extract the full content of an individual article"""
        if not article.article_url:
            logger.warning(f"⚠️ Cannot extract content: Missing article URL for {article.article_id}")
            return None
            
        logger.info(f"📄 Extracting content for article: {article.title}")
        
        try:
            # Navigate to the article page
            if not await self.navigate_to_url(article.article_url):
                return None
                
            # Simulate human behavior
            await self.human_simulator.simulate_user_behavior()
            
            # Wait for content to load with multiple selector options
            content_found = False
            for selector in self.config.content_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=self.config.timeout / len(self.config.content_selectors))
                    content_found = True
                    logger.info(f"✅ Content found with selector: {selector}")
                    break
                except PlaywrightTimeoutError:
                    logger.debug(f"⚠️ Selector not found: {selector}")
                    continue
                    
            if not content_found:
                logger.warning(f"❌ No content selectors matched for article: {article.article_id}")
                return None
                
            # Extract content using BeautifulSoup
            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try each selector
            content_text = None
            for selector in self.config.content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    content_text = content_element.get_text(strip=True)
                    if content_text:
                        break
            
            if content_text:
                logger.info(f"✅ Content extracted successfully ({len(content_text)} characters)")
                return content_text
            else:
                logger.warning(f"❌ Failed to extract content for article: {article.article_id}")
                return None
                
        except Exception as e:
            log_exception(
                logger,
                e,
                f"Error extracting content for article",
                {"article_id": article.article_id, "url": article.article_url}
            )
            return None

    async def scrape_article_list(self) -> List[Article]:
        """Scrape the list of articles from the main page"""
        articles = []
        url = f"{self.config.base_url}?category={self.config.category}"
        
        try:
            if not await self.navigate_to_url(url):
                logger.error("❌ Failed to navigate to article list page")
                return articles
                
            scroll_count = 0
            while scroll_count < self.config.max_scrolls and len(articles) < self.config.num_articles:
                # Simulate human scrolling behavior
                await self.human_simulator.simulate_scrolling()
                
                # Extract articles from the current page
                html_content = await self.page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Try multiple selectors for article elements
                article_elements = []
                
                # Try the original selectors
                article_elements = soup.find_all('article', class_='post-card') or soup.find_all('article', class_='jsx-216305209 post-card')
                
                # If no articles found, try more generic selectors
                if not article_elements:
                    # Try any article element
                    article_elements = soup.find_all('article')
                    
                    # If still no articles, try divs that look like article cards
                    if not article_elements:
                        article_elements = soup.find_all('div', class_=lambda c: c and ('card' in c or 'article' in c or 'post' in c))
                
                logger.info(f"📋 Found {len(article_elements)} article elements on page")
                
                for article_element in article_elements:
                    article = self.parse_article(article_element)
                    if article and self._is_valid_article(article) and article.article_id not in self.processed_article_ids:
                        articles.append(article)
                        self.processed_article_ids.add(article.article_id)
                        
                        if len(articles) >= self.config.num_articles:
                            logger.info(f"✅ Reached target number of articles: {self.config.num_articles}")
                            break
                
                scroll_count += 1
                logger.info(f"📜 Scroll {scroll_count}/{self.config.max_scrolls} complete. Articles found so far: {len(articles)}")
                
                # Add a small delay between scrolls
                await asyncio.sleep(random.uniform(*self.config.url_delay_range))
                
            return articles
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error scraping article list",
                {"url": url, "scroll_count": scroll_count, "articles_found": len(articles)}
            )
            return articles

    async def scrape_article_contents(self, articles: List[Article]) -> List[Article]:
        """Scrape the full content for each article"""
        articles_with_content = []
        
        try:
            for i, article in enumerate(articles):
                logger.info(f"🔄 Processing article {i+1}/{len(articles)}: {article.title}")
                
                # Extract the full content
                content = await self.extract_article_content(article)
                
                if content:
                    # Create a new article with content
                    article_with_content = Article(**article.model_dump(), content=content)
                    articles_with_content.append(article_with_content)
                else:
                    logger.warning(f"⚠️ Failed to extract content for article: {article.article_id}")
                    self.incomplete_articles += 1
                    
                # Add a delay between article requests to avoid rate limiting
                if i < len(articles) - 1:  # Don't delay after the last article
                    delay = random.uniform(*self.config.url_delay_range)
                    logger.info(f"⏱️ Waiting {delay:.2f}s before next article...")
                    await asyncio.sleep(delay)
                    
            return articles_with_content
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error scraping article contents",
                {"total_articles": len(articles), "processed_articles": len(articles_with_content)}
            )
            return articles_with_content

    def save_to_csv(self, articles: List[Article]) -> str:
        """Save articles to a CSV file"""
        if not articles:
            logger.warning("⚠️ No articles to save")
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_num = 0  # You could implement batch numbering if needed
        filename = f"{self.config.filename_prefix}_batch_{batch_num}_{timestamp}.csv"
        filepath = os.path.join(self.config.output_dir, filename)
        
        try:
            # Convert articles to DataFrame
            articles_dict = [article.model_dump() for article in articles]
            return save_articles_to_csv(articles_dict, filepath)
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error saving articles to CSV",
                {"article_count": len(articles), "filepath": filepath}
            )
            return ""

    def save_to_json(self, articles: List[Article]) -> str:
        """Save articles to a JSON file"""
        if not articles:
            logger.warning("⚠️ No articles to save")
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_num = 0  # You could implement batch numbering if needed
        filename = f"{self.config.filename_prefix}_batch_{batch_num}_{timestamp}.json"
        filepath = os.path.join(self.config.output_dir, filename)
        
        try:
            # Convert articles to dict
            articles_dict = [article.model_dump() for article in articles]
            return save_articles_to_json(articles_dict, filepath)
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error saving articles to JSON",
                {"article_count": len(articles), "filepath": filepath}
            )
            return ""

    async def scrape(self) -> pd.DataFrame:
        """Main scraping function"""
        start_time = datetime.now()
        logger.info(f"🚀 Starting scraping at {start_time}")
        
        try:
            async with async_playwright() as playwright:
                await self.setup_browser(playwright)
                
                # Step 1: Scrape the list of articles
                articles = await self.scrape_article_list()
                self.total_articles = len(articles)
                
                if not articles:
                    logger.warning("⚠️ No articles found")
                    return pd.DataFrame()
                
                # Step 2: Scrape the content for each article (optional)
                articles_with_content = await self.scrape_article_contents(articles)
                
                # Step 3: Save the results
                self.save_to_csv(articles_with_content)
                self.save_to_json(articles_with_content)
                
                # Convert to DataFrame for API return
                articles_dict = [article.model_dump() for article in articles_with_content]
                df = pd.DataFrame(articles_dict)
                
                end_time = datetime.now()
                log_summary(
                    self.total_articles, 
                    self.processed_article_ids, 
                    self.incomplete_articles, 
                    start_time, 
                    end_time,
                    self.config.model_dump()
                )
                
                return df
                
        except Exception as e:
            end_time = datetime.now()
            log_exception(
                logger,
                e,
                "Error during scraping process",
                {
                    "duration": (end_time - start_time).total_seconds(),
                    "articles_found": getattr(self, 'total_articles', 0),
                    "articles_processed": len(getattr(self, 'processed_article_ids', set())),
                    "config": self.config.model_dump()
                }
            )
            return pd.DataFrame() 