# app/scraper/parser.py
import re
from typing import Optional, Tuple, List
from bs4 import BeautifulSoup
from app.models import Article, ScraperConfig
from app.logger import get_logger, log_exception
from dateutil import parser as date_parser

# Get the logger instance
logger = get_logger()

class ArticleParser:
    """Parses HTML content to extract article information"""
    def __init__(self, config: ScraperConfig):
        """Initialize the parser with configuration"""
        self.config = config
        logger.info(f"Initialized ArticleParser with category: {self.config.category}")

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
                    dt = date_parser.parse(time_element.get('datetime'))
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

    def is_valid_article(self, article: Article) -> bool:
        """Validate if the article has all required fields"""
        if not article.article_url:
            logger.warning(f"⚠️ Skipping article with missing article_url: {article.article_id}")
            return False
        return True

    def clean_article_data(self, article: Article) -> Article:
        """Clean and normalize article data"""
        return article
