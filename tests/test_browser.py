# tests/test_browser.py
import unittest
from unittest.mock import MagicMock, patch, AsyncMock, call
import asyncio
import os
import sys

from app.models import ScraperConfig
from app.scraper.browser import BrowserManager

class TestBrowserManager(unittest.TestCase):
    """Test cases for the BrowserManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ScraperConfig(
            category="artificial-intelligence",
            base_url="https://www.techinasia.com/news",
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Mock the playwright components
        self.mock_playwright = MagicMock()
        self.mock_browser = MagicMock()
        self.mock_context = MagicMock()
        self.mock_page = MagicMock()
        
        # Set up the mock chain
        self.mock_playwright.chromium.launch = AsyncMock(return_value=self.mock_browser)
        self.mock_browser.new_context = AsyncMock(return_value=self.mock_context)
        self.mock_context.new_page = AsyncMock(return_value=self.mock_page)
        
        # Mock the page methods
        self.mock_page.goto = AsyncMock(return_value=None)
        self.mock_page.wait_for_load_state = AsyncMock()
        self.mock_page.wait_for_selector = AsyncMock()
        
        # Create the browser manager
        self.browser_manager = BrowserManager(self.config)
        
        # Mock the human simulator
        self.mock_human_simulator = MagicMock()
        self.mock_human_simulator.simulate_user_behavior = AsyncMock()
    
    @patch('app.human_behavior.HumanBehaviorSimulator')
    async def async_setup_browser(self, mock_human_simulator_class):
        """Async helper to set up the browser."""
        mock_human_simulator_class.return_value = self.mock_human_simulator
        
        # Set up the browser manager
        await self.browser_manager.setup_browser(self.mock_playwright)
        return self.browser_manager
    
    def test_initialization(self):
        """Test BrowserManager initialization."""
        self.assertEqual(self.browser_manager.config, self.config)
        self.assertIsNone(self.browser_manager.browser)
        self.assertIsNone(self.browser_manager.page)
        self.assertIsNone(self.browser_manager.human_simulator)
    
    @patch('app.human_behavior.HumanBehaviorSimulator')
    def test_setup_browser(self, mock_human_simulator_class):
        """Test browser setup."""
        mock_human_simulator_class.return_value = self.mock_human_simulator
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.browser_manager.setup_browser(self.mock_playwright))
        
        self.assertTrue(result)
        # Verify the browser was launched with correct parameters
        self.mock_playwright.chromium.launch.assert_called_once_with(headless=True)
        
        # Verify context was created
        self.mock_browser.new_context.assert_called_once()
        
        # Verify page was created
        self.mock_context.new_page.assert_called_once()
        
        # Verify browser manager state
        self.assertEqual(self.browser_manager.browser, self.mock_browser)
        self.assertEqual(self.browser_manager.page, self.mock_page)
        self.assertEqual(self.browser_manager.human_simulator, self.mock_human_simulator)
    
    @patch('app.human_behavior.HumanBehaviorSimulator')
    def test_navigate_to_url_success(self, mock_human_simulator_class):
        """Test successful navigation to URL."""
        mock_human_simulator_class.return_value = self.mock_human_simulator
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.browser_manager.setup_browser(self.mock_playwright))
        
        # Reset mock calls from initialization
        self.mock_page.goto.reset_mock()
        
        # Test navigation
        test_url = "https://www.techinasia.com/test-article"
        success = loop.run_until_complete(self.browser_manager.navigate_to_url(test_url))
        
        self.assertTrue(success)
        self.mock_page.goto.assert_called_once_with(test_url, timeout=self.config.timeout)
    
    @patch('app.human_behavior.HumanBehaviorSimulator')
    def test_navigate_to_url_failure(self, mock_human_simulator_class):
        """Test navigation failure."""
        mock_human_simulator_class.return_value = self.mock_human_simulator
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.browser_manager.setup_browser(self.mock_playwright))
        
        # Make goto raise an exception
        self.mock_page.goto.side_effect = Exception("Navigation failed")
        
        # Test navigation
        test_url = "https://www.techinasia.com/test-article"
        success = loop.run_until_complete(self.browser_manager.navigate_to_url(test_url))
        
        self.assertFalse(success)
        # Update assertion to account for retry mechanism (5 attempts)
        self.assertEqual(self.mock_page.goto.call_count, self.config.retry_count)
        # Verify all calls were made with the same parameters
        for call_args in self.mock_page.goto.call_args_list:
            self.assertEqual(call_args, call(test_url, timeout=self.config.timeout))
    
    @patch('app.human_behavior.HumanBehaviorSimulator')
    def test_close(self, mock_human_simulator_class):
        """Test browser closing."""
        mock_human_simulator_class.return_value = self.mock_human_simulator
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.browser_manager.setup_browser(self.mock_playwright))
        
        # Reset mock calls from initialization
        self.mock_browser.close.reset_mock()
        
        # Test closing
        loop.run_until_complete(self.browser_manager.close())
        
        self.mock_browser.close.assert_called_once()

if __name__ == '__main__':
    unittest.main() 