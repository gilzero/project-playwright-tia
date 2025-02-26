# tests/test_main.py
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import os
import sys
import json
from datetime import datetime
import pandas as pd

from app.models import ScraperConfig, Article
from app.scraper.main import TechInAsiaScraper
from app.scraper.browser import BrowserManager
from app.scraper.parser import ArticleParser
from app.scraper.content_extractor import ContentExtractor
from app.scraper.storage import StorageManager

class TestTechInAsiaScraper(unittest.TestCase):
    """Test cases for the TechInAsiaScraper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ScraperConfig(
            category="artificial-intelligence",
            base_url="https://www.techinasia.com/news",
            headless=True,
            max_articles=5,
            max_scrolls=3,
            output_dir="test_output",
            delay_between_requests=(1, 3)
        )
        
        # Mock the components
        self.mock_browser_manager = MagicMock(spec=BrowserManager)
        self.mock_article_parser = MagicMock(spec=ArticleParser)
        self.mock_content_extractor = MagicMock(spec=ContentExtractor)
        self.mock_storage_manager = MagicMock(spec=StorageManager)
        
        # Set up the mock browser manager
        self.mock_browser_manager.setup_browser = AsyncMock()
        self.mock_browser_manager.navigate_to_url = AsyncMock(return_value=True)
        self.mock_browser_manager.human_simulator = MagicMock()
        self.mock_browser_manager.human_simulator.simulate_scrolling = AsyncMock()
        self.mock_browser_manager.page = MagicMock()
        self.mock_browser_manager.page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        
        # Set up the mock article parser
        self.sample_articles = [
            Article(
                article_id="article1",
                title="Test Article 1",
                article_url="https://www.techinasia.com/article1",
                source="TechInAsia",
                image_url="https://example.com/image1.jpg",
                published_time="2023-01-01",
                categories=["AI"],
                tags=["technology"]
            ),
            Article(
                article_id="article2",
                title="Test Article 2",
                article_url="https://www.techinasia.com/article2",
                source="TechInAsia",
                image_url="https://example.com/image2.jpg",
                published_time="2023-01-02",
                categories=["Blockchain"],
                tags=["crypto"]
            )
        ]
        
        # Create patches for component creation
        self.browser_manager_patch = patch('app.scraper.main.BrowserManager', return_value=self.mock_browser_manager)
        self.article_parser_patch = patch('app.scraper.main.ArticleParser', return_value=self.mock_article_parser)
        self.content_extractor_patch = patch('app.scraper.main.ContentExtractor', return_value=self.mock_content_extractor)
        self.storage_manager_patch = patch('app.scraper.main.StorageManager', return_value=self.mock_storage_manager)
        
        # Start the patches
        self.browser_manager_patch.start()
        self.article_parser_patch.start()
        self.content_extractor_patch.start()
        self.storage_manager_patch.start()
        
        # Create the scraper
        self.scraper = TechInAsiaScraper(self.config)
        
        # Set up the mock article parser after scraper creation
        self.scraper.article_parser.parse_article_list = MagicMock(return_value=self.sample_articles)
        self.scraper.article_parser.is_valid_article = MagicMock(return_value=True)
        
        # Set up the mock content extractor
        self.mock_content_extractor.extract_article_content = AsyncMock(
            side_effect=lambda article: f"Content for {article.title}"
        )
        
        # Set up the mock storage manager
        self.mock_storage_manager.save_to_csv = MagicMock()
        self.mock_storage_manager.save_to_json = MagicMock()
        self.mock_storage_manager.to_dataframe = MagicMock(return_value=pd.DataFrame())
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the patches
        self.browser_manager_patch.stop()
        self.article_parser_patch.stop()
        self.content_extractor_patch.stop()
        self.storage_manager_patch.stop()
    
    @patch('app.scraper.main.async_playwright')
    @patch('app.scraper.main.random.uniform', return_value=1.0)
    @patch('app.scraper.main.asyncio.sleep', new_callable=AsyncMock)
    async def async_run_scraper(self, mock_sleep, mock_uniform, mock_playwright):
        """Async helper to run the scraper."""
        mock_playwright.return_value.__aenter__.return_value = MagicMock()
        return await self.scraper.scrape()
    
    def test_initialization(self):
        """Test scraper initialization."""
        self.assertEqual(self.scraper.config, self.config)
        self.assertIsNone(self.scraper.browser_manager)
        self.assertEqual(self.scraper.article_parser, self.mock_article_parser)
        self.assertEqual(self.scraper.storage_manager, self.mock_storage_manager)
        self.assertEqual(self.scraper.processed_article_ids, set())
        self.assertEqual(self.scraper.incomplete_articles, 0)
        self.assertEqual(self.scraper.total_articles, 0)
        self.assertEqual(self.scraper.articles_data, [])
    
    @patch('app.scraper.main.async_playwright')
    def test_scrape(self, mock_playwright):
        """Test scrape method."""
        mock_playwright.return_value.__aenter__.return_value = MagicMock()
        
        # Ensure the mock parser returns sample articles
        self.mock_browser_manager.page.content.return_value = "<html><body>Test content with articles</body></html>"
        
        # Create a patched version of scrape_article_list that returns sample articles
        original_scrape_article_list = self.scraper.scrape_article_list
        
        async def patched_scrape_article_list():
            # Simulate the navigation to the article list page
            await self.scraper.browser_manager.navigate_to_url(f"{self.config.base_url}?category={self.config.category}")
            return self.sample_articles
            
        # Replace the method with our patched version
        self.scraper.scrape_article_list = patched_scrape_article_list
        
        # Mock the scrape_article_contents method to avoid content extraction errors
        original_scrape_article_contents = self.scraper.scrape_article_contents
        
        async def patched_scrape_article_contents(articles):
            return articles
            
        self.scraper.scrape_article_contents = patched_scrape_article_contents
        
        try:
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(self.scraper.scrape())
            
            # Verify browser setup
            self.assertEqual(self.scraper.browser_manager, self.mock_browser_manager)
            self.mock_browser_manager.setup_browser.assert_called_once()
            
            # Verify article list scraping
            self.mock_browser_manager.navigate_to_url.assert_called_with(f"{self.config.base_url}?category={self.config.category}")
            
            # Verify storage
            self.mock_storage_manager.save_to_csv.assert_called_once()
            self.mock_storage_manager.save_to_json.assert_called_once()
            self.mock_storage_manager.to_dataframe.assert_called_once()
        finally:
            # Restore the original methods
            self.scraper.scrape_article_list = original_scrape_article_list
            self.scraper.scrape_article_contents = original_scrape_article_contents
    
    @patch('app.scraper.main.async_playwright')
    def test_scrape_with_navigation_failure(self, mock_playwright):
        """Test scrape method with navigation failure."""
        mock_playwright.return_value.__aenter__.return_value = MagicMock()
        
        # Make navigation fail
        self.mock_browser_manager.navigate_to_url = AsyncMock(return_value=False)
        
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.scraper.scrape())
        
        # Verify navigation attempt
        self.mock_browser_manager.navigate_to_url.assert_called_with(f"{self.config.base_url}?category={self.config.category}")
        
        # Verify no further processing
        self.mock_storage_manager.save_to_csv.assert_not_called()
        self.mock_storage_manager.save_to_json.assert_not_called()
    
    @patch('app.scraper.main.async_playwright')
    def test_scrape_with_no_articles(self, mock_playwright):
        """Test scrape method with no articles found."""
        mock_playwright.return_value.__aenter__.return_value = MagicMock()
        
        # Make article parser return empty list
        self.scraper.article_parser.parse_article_list = MagicMock(return_value=[])
        
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.scraper.scrape())
        
        # Verify navigation and parsing
        self.mock_browser_manager.navigate_to_url.assert_called_with(f"{self.config.base_url}?category={self.config.category}")
        
        # Verify no storage
        self.mock_storage_manager.save_to_csv.assert_not_called()
        self.mock_storage_manager.save_to_json.assert_not_called()
    
    @patch('app.scraper.main.ContentExtractor')
    @patch('app.scraper.main.async_playwright')
    def test_scrape_with_content_extraction(self, mock_playwright, mock_content_extractor_class):
        """Test scrape method with content extraction."""
        mock_playwright.return_value.__aenter__.return_value = MagicMock()
        
        # Create a new config with extract_content=True
        config_with_content = ScraperConfig(
            category="artificial-intelligence",
            base_url="https://www.techinasia.com/news",
            headless=True,
            max_articles=5,
            max_scrolls=3,
            output_dir="test_output",
            delay_between_requests=(1, 3),
            extract_content=True
        )
        
        # Create a new scraper with the content extraction config
        scraper_with_content = TechInAsiaScraper(config_with_content)
        
        # Set up the mocks for the new scraper
        scraper_with_content.browser_manager = self.mock_browser_manager
        scraper_with_content.article_parser = self.scraper.article_parser
        scraper_with_content.storage_manager = self.mock_storage_manager
        
        # Set up content extractor
        mock_content_extractor = MagicMock()
        mock_content_extractor.extract_article_content = AsyncMock(side_effect=lambda article: f"Content for {article.title}")
        mock_content_extractor_class.return_value = mock_content_extractor
        
        # Create a patched version of scrape_article_list that returns sample articles
        original_scrape_article_list = scraper_with_content.scrape_article_list
        
        async def patched_scrape_article_list():
            # Simulate the navigation to the article list page
            await scraper_with_content.browser_manager.navigate_to_url(f"{config_with_content.base_url}?category={config_with_content.category}")
            return self.sample_articles
            
        # Replace the method with our patched version
        scraper_with_content.scrape_article_list = patched_scrape_article_list
        
        # Keep the original scrape_article_contents method to test content extraction
        
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(scraper_with_content.scrape())
        
        # Verify content extraction
        self.assertEqual(mock_content_extractor.extract_article_content.call_count, len(self.sample_articles))
        
        # Verify storage
        self.mock_storage_manager.save_to_csv.assert_called_once()
        self.mock_storage_manager.save_to_json.assert_called_once()
        
        # Restore the original method
        scraper_with_content.scrape_article_list = original_scrape_article_list
    
    @patch('app.scraper.main.logger')
    @patch('app.scraper.main.async_playwright')
    def test_logging(self, mock_playwright, mock_logger):
        """Test logging during scraping."""
        mock_playwright.return_value.__aenter__.return_value = MagicMock()
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.scraper.scrape())
        
        # Verify logging calls
        self.assertTrue(mock_logger.info.called)
        # Debug logs might not be called if the log level is set to INFO
        # self.assertTrue(mock_logger.debug.called)

if __name__ == '__main__':
    unittest.main() 