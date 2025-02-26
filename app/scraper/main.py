# app/scraper/main.py
import asyncio
import random
from typing import List, Set
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.models import Article, ScraperConfig
from app.logger import get_logger, log_exception, log_summary
from app.utils import setup_output_directory

from app.scraper.browser import BrowserManager
from app.scraper.parser import ArticleParser
from app.scraper.content_extractor import ContentExtractor
from app.scraper.storage import StorageManager

# Get the logger instance
logger = get_logger()

class TechInAsiaScraper:
    """Main scraper class that orchestrates the scraping process"""
    def __init__(self, config: ScraperConfig):
        """Initialize the scraper with configuration"""
        self.config = config
        setup_output_directory(self.config.output_dir)
        
        # Initialize components
        self.browser_manager = None
        self.article_parser = ArticleParser(config)
        self.storage_manager = StorageManager(config)
        
        # State tracking
        self.processed_article_ids = set()
        self.incomplete_articles = 0
        self.total_articles = 0
        self.articles_data = []
        
        logger.info(f"Initialized TechInAsiaScraper with category: {self.config.category}")
        logger.debug(f"Scraper configuration: {self.config.model_dump_json()}")

    async def scrape_article_list(self) -> List[Article]:
        """Scrape the list of articles from the main page"""
        articles = []
        url = f"{self.config.base_url}?category={self.config.category}"
        
        try:
            if not await self.browser_manager.navigate_to_url(url):
                logger.error("❌ Failed to navigate to article list page")
                return articles
                
            scroll_count = 0
            while scroll_count < self.config.max_scrolls and len(articles) < self.config.num_articles:
                # Simulate human scrolling behavior
                await self.browser_manager.human_simulator.simulate_scrolling()
                
                # Extract articles from the current page
                html_content = await self.browser_manager.page.content()
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
                    article = self.article_parser.parse_article(article_element)
                    if article and self.article_parser.is_valid_article(article) and article.article_id not in self.processed_article_ids:
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
        content_extractor = ContentExtractor(self.browser_manager, self.config)
        
        try:
            for i, article in enumerate(articles):
                logger.info(f"🔄 Processing article {i+1}/{len(articles)}: {article.title}")
                
                # Extract the full content
                content = await content_extractor.extract_article_content(article)
                
                if content:
                    # Create a new article with content
                    article_data = article.model_dump()
                    article_data['content'] = content
                    article_with_content = Article(**article_data)
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

    async def scrape(self) -> pd.DataFrame:
        """Main scraping function"""
        start_time = datetime.now()
        logger.info(f"🚀 Starting scraping at {start_time}")
        
        try:
            async with async_playwright() as playwright:
                # Initialize browser
                self.browser_manager = BrowserManager(self.config)
                await self.browser_manager.setup_browser(playwright)
                
                # Step 1: Scrape the list of articles
                articles = await self.scrape_article_list()
                self.total_articles = len(articles)
                
                if not articles:
                    logger.warning("⚠️ No articles found")
                    return pd.DataFrame()
                
                # Reset the processed_article_ids set to allow content extraction
                # for all articles found in this run
                self.processed_article_ids = set()
                
                # Step 2: Scrape the content for each article
                articles_with_content = await self.scrape_article_contents(articles)
                
                # Step 3: Save the results
                if articles_with_content:
                    self.storage_manager.save_to_csv(articles_with_content)
                    self.storage_manager.save_to_json(articles_with_content)
                    
                    # Convert to DataFrame for API return
                    df = self.storage_manager.to_dataframe(articles_with_content)
                else:
                    logger.warning("⚠️ No articles with content to save")
                    df = pd.DataFrame()
                
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
