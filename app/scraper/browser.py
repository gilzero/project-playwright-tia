# app/scraper/browser.py
import random
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import Error as PlaywrightError
from app.models import ScraperConfig
from app.logger import get_logger, log_exception

# Get the logger instance
logger = get_logger()

class BrowserManager:
    """Manages browser initialization and navigation"""
    def __init__(self, config: ScraperConfig):
        """Initialize the browser manager with configuration"""
        self.config = config
        self.browser = None
        self.page = None
        self.human_simulator = None
        logger.info(f"Initialized BrowserManager")

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
            from app.human_behavior import HumanBehaviorSimulator
            self.human_simulator = HumanBehaviorSimulator(self.page, self.config)
            
            logger.info("🚀 Playwright browser initialized successfully")
            return True
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
                logger.warning(f"⚠️ Error navigating to {url}: {str(e)[:100]} (Attempt {attempt + 1}/{self.config.retry_count})")
                if attempt < self.config.retry_count - 1:
                    # Longer wait time for connection errors
                    wait_time = 3 ** attempt + random.uniform(1, 3)
                    logger.info(f"⏱️ Waiting {wait_time:.2f}s before retry due to connection error...")
                    await asyncio.sleep(wait_time)
                    
                    # Try to recreate the page if we had a connection error
                    if "Connection closed" in str(e):
                        try:
                            logger.info("Attempting to recreate browser page due to connection error...")
                            if self.page:
                                await self.page.close()
                            context = self.browser.contexts[0]
                            self.page = await context.new_page()
                            logger.info("Successfully recreated browser page")
                        except Exception as page_error:
                            logger.error(f"Failed to recreate page: {str(page_error)}")
                else:
                    log_exception(
                        logger,
                        e,
                        f"Error navigating to {url}",
                        {"url": url, "attempt": attempt + 1}
                    )
                    return False
        return False

    async def close(self):
        """Close the browser and clean up resources"""
        if self.browser:
            try:
                await self.browser.close()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.warning(f"Error closing browser: {str(e)}")
