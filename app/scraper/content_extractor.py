from typing import Optional
from bs4 import BeautifulSoup
from app.models import Article, ScraperConfig
from app.logger import get_logger, log_exception
from app.scraper.browser import BrowserManager

# Get the logger instance
logger = get_logger()

class ContentExtractor:
    """Extracts full content from article pages"""
    def __init__(self, browser_manager: BrowserManager, config: ScraperConfig):
        """Initialize the content extractor with browser manager and configuration"""
        self.browser_manager = browser_manager
        self.config = config
        logger.info(f"Initialized ContentExtractor")

    async def extract_article_content(self, article: Article) -> Optional[str]:
        """Extract the full content of an individual article from TechInAsia page"""
        logger.info(f"📄 Extracting content for article: {article.title}")
        
        try:
            # Construct the TechInAsia article URL based on the article ID
            # The article ID might be the full path or just the slug
            article_id = article.article_id
            
            # If the article_id contains a domain, it's likely a reference to an external source
            # We need to construct a proper TechInAsia URL
            if '.' in article_id and '/' not in article_id:
                # This is likely a domain-based ID like "restofworld.org"
                # Try to construct a URL from the title
                slug = article.title.lower().replace(' ', '-')
                tia_article_url = f"{self.config.base_url}/{slug}"
            elif article_id.startswith('http'):
                # If it's a full URL, extract the last part as the slug
                slug = article_id.split('/')[-1]
                tia_article_url = f"{self.config.base_url}/{slug}"
            else:
                # Otherwise use the article_id directly
                tia_article_url = f"{self.config.base_url}/{article_id}"
            
            logger.info(f"🌐 Extracting content from TechInAsia URL: {tia_article_url}")
            
            # Navigate to the TechInAsia article page
            if not await self.browser_manager.navigate_to_url(tia_article_url):
                # If direct navigation fails, try using the article URL as a fallback
                if article.article_url and article.article_url.startswith('https://www.techinasia.com'):
                    logger.info(f"🌐 Trying fallback URL: {article.article_url}")
                    if not await self.browser_manager.navigate_to_url(article.article_url):
                        logger.warning(f"⚠️ Failed to navigate to article page: {tia_article_url}")
                        return None
                else:
                    logger.warning(f"⚠️ Failed to navigate to article page: {tia_article_url}")
                    return None
                
            # Get the HTML content immediately after navigation
            html_content = await self.browser_manager.page.content()
            
            # Simulate human behavior - but don't fail if it errors
            try:
                await self.browser_manager.human_simulator.simulate_user_behavior()
                
                # Get the HTML content again after human behavior simulation
                try:
                    updated_html = await self.browser_manager.page.content()
                    if updated_html and len(updated_html) > len(html_content):
                        html_content = updated_html
                except Exception as e:
                    logger.warning(f"Error getting updated HTML after simulation: {str(e)[:100]}")
            except Exception as e:
                logger.warning(f"Error during human behavior simulation: {str(e)[:100]}")
            
            # TechInAsia specific selectors for article content
            tia_selectors = [
                "div.jsx-3810287742.jsx-430771670.content",  # Main content selector
                "div.content",                               # Generic content selector
                "article.post-content",                      # Article content
                "div.post-content",                          # Post content
                "div.article-content",                       # Article content
                "div.article__content",                      # Article content with BEM naming
                "div.post__content",                         # Post content with BEM naming
                "div#content",                               # Content by ID
                ".content",                                  # Content by class
                "article",                                   # Any article element
                "main"                                       # Main content area
            ]
            
            # Wait for content to load with TechInAsia specific selectors
            content_found = False
            for selector in tia_selectors:
                try:
                    # Use a shorter timeout for each selector
                    timeout = min(2000, self.config.timeout / len(tia_selectors))
                    await self.browser_manager.page.wait_for_selector(selector, timeout=timeout)
                    content_found = True
                    logger.info(f"✅ Content found with selector: {selector}")
                    
                    # Try to get updated HTML after finding content
                    try:
                        updated_html = await self.browser_manager.page.content()
                        if updated_html and len(updated_html) > len(html_content):
                            html_content = updated_html
                    except Exception as e:
                        logger.warning(f"Error getting updated HTML after finding content: {str(e)[:100]}")
                    
                    break
                except Exception as e:
                    logger.debug(f"⚠️ Selector not found: {selector}")
                    continue
            
            # If we couldn't find content with selectors but have HTML, try to extract anyway
            if not content_found and not html_content:
                logger.warning(f"❌ No content selectors matched and no HTML for article: {article.article_id}")
                return None
                
            # Extract content using BeautifulSoup
            content = self._extract_content_from_html(html_content, article.article_id)
            
            # If content is too short, it might be a summary or incomplete
            if content and len(content) < 200:
                logger.warning(f"⚠️ Content seems too short ({len(content)} chars), might be just a summary")
                
                # Try to extract content directly using JavaScript
                try:
                    js_content = await self._extract_content_with_js()
                    if js_content and len(js_content) > len(content):
                        logger.info(f"✅ Extracted better content using JavaScript ({len(js_content)} chars)")
                        content = js_content
                except Exception as e:
                    logger.warning(f"Error extracting content with JavaScript: {str(e)[:100]}")
            
            return content
                
        except Exception as e:
            log_exception(
                logger,
                e,
                f"Error extracting content for article",
                {"article_id": article.article_id, "title": article.title}
            )
            return None
    
    async def _extract_content_with_js(self) -> Optional[str]:
        """Extract content using JavaScript directly in the browser"""
        try:
            # JavaScript to extract text content from various selectors
            js_extract = """
            function extractContent() {
                // Try various selectors
                const selectors = [
                    'div.jsx-3810287742.jsx-430771670.content',
                    'div.content',
                    'article.post-content',
                    'div.post-content',
                    'div.article-content',
                    'div.article__content',
                    'div.post__content',
                    'div#content',
                    '.content',
                    'article',
                    'main'
                ];
                
                for (const selector of selectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        return element.innerText;
                    }
                }
                
                // If no selector matches, try to get all paragraphs
                const paragraphs = document.querySelectorAll('p');
                if (paragraphs.length > 0) {
                    return Array.from(paragraphs).map(p => p.innerText).join(' ');
                }
                
                return null;
            }
            return extractContent();
            """
            
            content = await self.browser_manager.page.evaluate(js_extract)
            return content
        except Exception as e:
            logger.warning(f"Error in JavaScript content extraction: {str(e)[:100]}")
            return None
            
    def _extract_content_from_html(self, html_content: str, article_id: str) -> Optional[str]:
        """Extract content from HTML using BeautifulSoup"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try each selector
            content_text = None
            
            # TechInAsia specific selectors
            tia_selectors = [
                "div.jsx-3810287742.jsx-430771670.content",  # Main content selector
                "div.content",                               # Generic content selector
                "article.post-content",                      # Article content
                "div.post-content",                          # Post content
                "div.article-content",                       # Article content
                "div.article__content",                      # Article content with BEM naming
                "div.post__content",                         # Post content with BEM naming
                "div#content",                               # Content by ID
                ".content",                                  # Content by class
                "article",                                   # Any article element
                "main"                                       # Main content area
            ]
            
            for selector in tia_selectors:
                try:
                    content_element = soup.select_one(selector)
                    if content_element:
                        content_text = content_element.get_text(strip=True)
                        if content_text:
                            logger.info(f"✅ Content extracted with TechInAsia selector: {selector}")
                            break
                except Exception as e:
                    logger.warning(f"Error with TechInAsia selector {selector}: {str(e)[:100]}")
            
            # If no content found with TechInAsia selectors, try configured selectors
            if not content_text:
                for selector in self.config.content_selectors:
                    try:
                        content_element = soup.select_one(selector)
                        if content_element:
                            content_text = content_element.get_text(strip=True)
                            if content_text:
                                logger.info(f"✅ Content extracted with configured selector: {selector}")
                                break
                    except Exception as e:
                        logger.debug(f"Error with configured selector {selector}: {str(e)[:100]}")
            
            # Last resort: try to get all paragraph text
            if not content_text:
                try:
                    paragraphs = soup.find_all('p')
                    if paragraphs:
                        content_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                        if content_text:
                            logger.info("✅ Content extracted from paragraphs as last resort")
                except Exception as e:
                    logger.warning(f"Error extracting paragraphs: {str(e)[:100]}")
            
            if content_text:
                # Clean up the content - remove common footer text
                footer_texts = [
                    "Copyright © 2025 Tech in Asia. All Rights Reserved.",
                    "A member ofThe Business Times.",
                    "If you're seeing this message, that meansJavaScript has been disabled on your browser.",
                    "Please enable JavaScript"
                ]
                
                for text in footer_texts:
                    content_text = content_text.replace(text, "")
                
                # Remove extra whitespace
                content_text = ' '.join(content_text.split())
                
                logger.info(f"✅ Content extracted successfully ({len(content_text)} characters)")
                return content_text
            else:
                logger.warning(f"❌ Failed to extract content for article: {article_id}")
                return None
                
        except Exception as e:
            log_exception(
                logger,
                e,
                f"Error extracting content from HTML",
                {"article_id": article_id, "html_length": len(html_content) if html_content else 0}
            )
            return None
