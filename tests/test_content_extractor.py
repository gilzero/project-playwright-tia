# tests/test_content_extractor.py
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from bs4 import BeautifulSoup
import os
import sys
import json

from app.models import ScraperConfig, Article
from app.scraper.content_extractor import ContentExtractor
from app.scraper.browser import BrowserManager

class TestContentExtractor(unittest.TestCase):
    """Test cases for the ContentExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ScraperConfig(
            category="artificial-intelligence",
            base_url="https://www.techinasia.com/news",
            content_selectors=["div.article-content", "div.post-content"]
        )
        
        # Mock the browser manager
        self.browser_manager = MagicMock(spec=BrowserManager)
        self.browser_manager.page = MagicMock()
        self.browser_manager.human_simulator = MagicMock()
        self.browser_manager.navigate_to_url = AsyncMock(return_value=True)
        self.browser_manager.page.content = AsyncMock(return_value=self.get_sample_article_html())
        self.browser_manager.page.wait_for_selector = AsyncMock()
        
        # Create the content extractor
        self.content_extractor = ContentExtractor(self.browser_manager, self.config)
        
        # Sample article
        self.article = Article(
            article_id="test-article",
            title="Test Article Title",
            article_url="https://www.techinasia.com/test-article"
        )
    
    def get_sample_article_html(self):
        """Get sample article HTML for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Article</title>
        </head>
        <body>
            <div class="article-content">
                <h1>Test Article Title</h1>
                <p>This is the first paragraph of the article content.</p>
                <p>This is the second paragraph with more detailed information.</p>
                <p>This is the conclusion of the article.</p>
            </div>
        </body>
        </html>
        """
    
    def get_sample_article_html_alternative(self):
        """Get alternative sample article HTML for testing fallback selectors."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Article</title>
        </head>
        <body>
            <div class="post-content">
                <h1>Test Article Title</h1>
                <p>This is the content in an alternative selector.</p>
            </div>
        </body>
        </html>
        """
    
    def get_sample_article_html_paragraphs_only(self):
        """Get sample article HTML with only paragraphs for testing last resort extraction."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Article</title>
        </head>
        <body>
            <p>This is the first paragraph of the article content.</p>
            <p>This is the second paragraph with more detailed information.</p>
            <p>This is the conclusion of the article.</p>
        </body>
        </html>
        """
    
    async def async_test(self, coroutine):
        """Helper method to run async tests."""
        return await coroutine
    
    def test_extract_content_from_html(self):
        """Test extracting content from HTML."""
        html = self.get_sample_article_html()
        article_id = "test-article"
        
        content = self.content_extractor._extract_content_from_html(html, article_id)
        
        self.assertIsNotNone(content)
        self.assertIn("This is the first paragraph", content)
        self.assertIn("This is the second paragraph", content)
        self.assertIn("This is the conclusion", content)
    
    def test_extract_content_from_html_alternative_selector(self):
        """Test extracting content from HTML using alternative selector."""
        html = self.get_sample_article_html_alternative()
        article_id = "test-article"
        
        content = self.content_extractor._extract_content_from_html(html, article_id)
        
        self.assertIsNotNone(content)
        self.assertIn("This is the content in an alternative selector", content)
    
    def test_extract_content_from_html_paragraphs_only(self):
        """Test extracting content from HTML with only paragraphs."""
        html = self.get_sample_article_html_paragraphs_only()
        article_id = "test-article"
        
        # Create a new content extractor with non-matching selectors
        config_with_nonmatching_selectors = ScraperConfig(
            category="artificial-intelligence",
            base_url="https://www.techinasia.com/news",
            content_selectors=["div.non-existent"]
        )
        content_extractor = ContentExtractor(self.browser_manager, config_with_nonmatching_selectors)
        
        content = content_extractor._extract_content_from_html(html, article_id)
        
        self.assertIsNotNone(content)
        self.assertIn("This is the first paragraph", content)
        self.assertIn("This is the second paragraph", content)
        self.assertIn("This is the conclusion", content)
    
    @patch('app.scraper.content_extractor.BeautifulSoup')
    def test_extract_content_from_html_with_exception(self, mock_bs):
        """Test handling exceptions when extracting content from HTML."""
        mock_bs.side_effect = Exception("Test exception")
        
        html = self.get_sample_article_html()
        article_id = "test-article"
        
        content = self.content_extractor._extract_content_from_html(html, article_id)
        
        self.assertIsNone(content)
    
    def test_extract_article_content(self):
        """Test extracting article content."""
        # Make the human simulator's simulate_user_behavior method awaitable
        self.browser_manager.human_simulator.simulate_user_behavior = AsyncMock()
        
        loop = asyncio.get_event_loop()
        content = loop.run_until_complete(
            self.content_extractor.extract_article_content(self.article)
        )
        
        self.assertIsNotNone(content)
        self.assertIn("This is the first paragraph", content)
        self.assertIn("This is the second paragraph", content)
        self.assertIn("This is the conclusion", content)
        
        # Verify method calls
        self.browser_manager.navigate_to_url.assert_called_once_with(self.article.article_url)
        self.browser_manager.human_simulator.simulate_user_behavior.assert_called_once()
        self.browser_manager.page.content.assert_called()
    
    def test_extract_article_content_navigation_failed(self):
        """Test extracting article content when navigation fails."""
        self.browser_manager.navigate_to_url = AsyncMock(return_value=False)
        
        loop = asyncio.get_event_loop()
        content = loop.run_until_complete(
            self.content_extractor.extract_article_content(self.article)
        )
        
        self.assertIsNone(content)
        self.browser_manager.navigate_to_url.assert_called_once_with(self.article.article_url)
        self.browser_manager.human_simulator.simulate_user_behavior.assert_not_called()
    
    def test_extract_article_content_missing_url(self):
        """Test extracting article content with missing URL."""
        article_without_url = Article(
            article_id="test-article",
            title="Test Article Title",
            article_url=None
        )
        
        loop = asyncio.get_event_loop()
        content = loop.run_until_complete(
            self.content_extractor.extract_article_content(article_without_url)
        )
        
        self.assertIsNone(content)
        self.browser_manager.navigate_to_url.assert_not_called()
    
    def test_extract_article_content_with_exception(self):
        """Test handling exceptions when extracting article content."""
        self.browser_manager.navigate_to_url = AsyncMock(side_effect=Exception("Test exception"))
        
        loop = asyncio.get_event_loop()
        content = loop.run_until_complete(
            self.content_extractor.extract_article_content(self.article)
        )
        
        self.assertIsNone(content)
        self.browser_manager.navigate_to_url.assert_called_once_with(self.article.article_url)

if __name__ == '__main__':
    unittest.main() 