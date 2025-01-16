# app/core.py
import time
import re
from typing import List, Optional
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from random import uniform
from app.models import Article, ScraperConfig
from app.utils import setup_output_directory, setup_logging
from tqdm import tqdm
from playwright.async_api import Error as PlaywrightError
from datetime import datetime
import asyncio

logger = setup_logging()

class ScrollManager:
    """Manages page scrolling"""
    def __init__(self, page, config: ScraperConfig):
        self.page = page
        self.config = config

    async def scroll_page(self) -> bool:
        """Scroll the page and return True if new content was loaded"""
        last_height = await self.page.evaluate("document.body.scrollHeight")
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await asyncio.sleep(uniform(self.config.min_delay, self.config.max_delay))
        new_height = await self.page.evaluate("document.body.scrollHeight")
        return new_height > last_height

class TechInAsiaScraper:
    def __init__(self, config: ScraperConfig):
        """Initialize the scraper with configuration"""
        self.config = config
        self.browser = None
        self.page = None
        self.scroll_manager = None
        setup_output_directory(self.config.output_dir)
        self.processed_article_ids = set()
        self.incomplete_articles = 0
        self.total_articles = 0

    async def setup_browser(self, playwright):
            """Initialize Playwright browser and page with retry mechanism"""
            try:
                self.browser = await playwright.chromium.launch(headless=True)
                self.page = await self.browser.new_page(user_agent=self.config.user_agent)
                self.scroll_manager = ScrollManager(self.page, self.config)
                logger.info("🚀 Playwright browser initialized successfully")
            except PlaywrightError as e:
                logger.error(f"😞 Playwright error during browser initialization: {e}")
                raise
            except Exception as e:
                logger.error(f"😞 Unexpected error during browser initialization: {e}")
                raise

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
            content_div = article_element.find('div', class_='post-content')
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
            logger.warning(f"⚠️ AttributeError parsing article: {article_element}, error: {e}")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Error parsing article: {article_element}, error: {e}")
            return None

    def _extract_article_id_and_url(self, content_div) -> tuple[Optional[str], Optional[str]]:
        """Extract article ID and URL"""
        article_links = [a for a in content_div.find_all('a') if not 'post-source' in a.get('class', [])]
        if article_links:
            href = article_links[0]['href']
            article_url = f"https://www.techinasia.com{href}" if not href.startswith('http') else href
            match = re.search(r'/([^/]+)$', href)
            article_id = match.group(1) if match else None
            logger.info(f"Parsing article: {article_id}")
            return article_id, article_url
        else:
            logger.warning("No article links found.")
            return None, None

    def _extract_title(self, content_div) -> Optional[str]:
        """Extract the title of the article"""
        title_element = content_div.find('h3', class_='post-title')
        return title_element.text.strip() if title_element else None

    def _extract_source_info(self, content_div) -> tuple[Optional[str], Optional[str]]:
        """Extract source name and URL"""
        logger.info(f"  - 📰 Extracting source...")
        source_element = content_div.find('span', class_='post-source-name')
        source = source_element.text.strip() if source_element else None
        logger.info(f"  - ✅ Source extracted: {source}")

        source_link = content_div.find('a', class_='post-source')
        source_url = source_link.get('href') if source_link else None
        logger.info(f"  - 🌐 Source URL extracted: {source_url}")
        return source, source_url

    def _extract_image_url(self, article_element) -> Optional[str]:
        """Extract image URL"""
        logger.info(f"  - 🖼️ Extracting image URL...")
        image_div = article_element.find('div', class_='post-image')
        if image_div:
            img_tag = image_div.find('img')
            image_url = img_tag.get('src') if img_tag else None
            logger.info(f"  - 🖼️ Image URL extracted: {image_url}")
            return image_url
        else:
            logger.warning(f"  - 🖼️ No image div found.")
            return None

    def _extract_time_info(self, article_element) -> tuple[Optional[str], Optional[str]]:
        """Extract posted time and relative time"""
        logger.info(f"  - ⏰ Extracting time and categories/tags...")
        footer = article_element.find('div', class_='post-footer')
        time_element = footer.find('time') if footer else None
        posted_time = time_element.get('datetime') if time_element else None
        relative_time = time_element.text.strip() if time_element else None
        logger.info(f"  - ⏰ Time extracted: {posted_time}, Relative Time: {relative_time}")
        return posted_time, relative_time

    def _extract_categories_and_tags(self, article_element) -> tuple[List[str], List[str]]:
        """Extract categories and tags"""
        categories = []
        tags = []
        footer = article_element.find('div', class_='post-footer')
        if footer:
            tag_elements = footer.find_all('a', class_='post-taxonomy-link')
            for tag in tag_elements:
                tag_text = tag.text.strip('· ')
                if tag_text:
                    if tag.get('href', '').startswith('/category/'):
                        categories.append(tag_text)
                    elif tag.get('href', '').startswith('/tag/'):
                        tags.append(tag_text)
            logger.info(f"  - 🏷️ Categories: {categories}, Tags: {tags}")
        return categories, tags

    async def scrape(self) -> pd.DataFrame:
        """Main scraping method"""
        articles = []
        start_time = datetime.now()
        try:
            async with async_playwright() as playwright:
                await self.setup_browser(playwright)
                articles = await self._scrape_with_retry()
                df = self._process_articles(articles)
                return df
        finally:
            if self.browser:
                await self.browser.close()
            end_time = datetime.now()
            from app.utils import log_summary
            log_summary(logger, self.total_articles, self.processed_article_ids, self.incomplete_articles, start_time, end_time)

    async def _scrape_with_retry(self) -> List[Article]:
        """Implement retry logic for scraping"""
        for attempt in range(self.config.retry_count):
            try:
                return await self._perform_scraping()
            except PlaywrightTimeoutError as e:
                logger.warning(f"Attempt {attempt + 1} failed due to timeout: {e}, retrying...")
            except PlaywrightError as e:
                logger.warning(f"Attempt {attempt + 1} failed due to Playwright error: {e}, retrying...")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed due to unexpected error: {e}, retrying...")
            if attempt == self.config.retry_count - 1:
                raise
            await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff

    async def _perform_scraping(self) -> List[Article]:
        """Perform the actual scraping"""
        articles = []
        url = f"{self.config.base_url}?category={self.config.category}"

        logger.info(f"Navigating to URL: {url}")
        try:
            await self.page.goto(url, timeout=self.config.timeout * 1000)  # Convert seconds to milliseconds
            await self.page.wait_for_selector('article.post-card', state='attached', timeout=self.config.timeout * 1000)
            logger.info(f"Page loaded successfully.")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while loading page: {e}")
            return articles
        except PlaywrightError as e:
            logger.error(f"Playwright error while loading page: {e}")
            return articles
        except Exception as e:
            logger.error(f"Unexpected error while loading page: {e}")
            return articles

        progress_bar = tqdm(total=self.config.num_articles, desc="Scraping Articles", unit="article")
        scroll_count = 0
        last_article_count = 0
        while len(articles) < self.config.num_articles and scroll_count < self.config.max_scrolls:
            soup = BeautifulSoup(await self.page.content(), 'html.parser')
            article_elements = soup.find_all('article', class_='post-card')

            for article_element in article_elements:
                try:
                    article = self.parse_article(article_element)
                    if article and article.article_id not in self.processed_article_ids:
                        if self._is_valid_article(article):
                            cleaned_article = self._clean_article_data(article)
                            articles.append(cleaned_article)
                            self.processed_article_ids.add(article.article_id)
                            logger.info(f"Processed article {article.article_id} - {article.title}")
                            progress_bar.update(1)
                            progress_bar.set_postfix({"incomplete": self.incomplete_articles})
                        else:
                            self.incomplete_articles += 1
                        self.total_articles += 1
                        if len(articles) >= self.config.num_articles:
                            break
                except Exception as e:
                    logger.error(f"Error during article processing: {e}")
                    continue

            if not await self.scroll_manager.scroll_page() or len(articles) == last_article_count:
                break
            last_article_count = len(articles)
            scroll_count += 1
            logger.info(f"Scrolled {scroll_count} times, found {len(articles)} articles")

            # Implementing rate limiting
            await asyncio.sleep(uniform(self.config.min_delay, self.config.max_delay))

        progress_bar.close()
        return articles

    def _process_articles(self, articles: List[Article]) -> pd.DataFrame:
        """Process and clean scraped articles"""
        if not articles:
            return pd.DataFrame()

        # Convert articles to DataFrame
        df = pd.DataFrame([article.model_dump() for article in articles])

        # Remove duplicates
        df = df.drop_duplicates(subset=['article_url'], keep='first')

        # Save in batches
        self._save_batches(df)

        return df

    def _save_batches(self, df: pd.DataFrame):
        """Save DataFrame in batches"""
        batch_size = self.config.batch_size
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_prefix = getattr(self.config, 'filename_prefix', "techinasia_ai_news")
        for i in range(0, len(df), batch_size):
            batch = df[i:i + batch_size]
            filename = f"{self.config.output_dir}/{filename_prefix}_batch_{i//batch_size}_{timestamp}.csv"
            try:
                batch.to_csv(filename, index=False)
                logger.info(f"Saved batch {i//batch_size + 1} to {filename}")
            except Exception as e:
                logger.error(f"Error saving batch {i//batch_size + 1} to {filename}: {e}")