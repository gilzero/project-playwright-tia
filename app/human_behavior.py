# app/human_behavior.py
import random
import asyncio
from app.models import ScraperConfig
from app.logger import get_logger, log_exception

# Get the logger instance
logger = get_logger()

class HumanBehaviorSimulator:
    """Simulates human-like behavior to avoid detection"""
    def __init__(self, page, config: ScraperConfig):
        self.page = page
        self.config = config
        logger.debug(f"Initialized HumanBehaviorSimulator with config: {config.model_dump_json()}")

    async def simulate_scrolling(self):
        """Simulate human-like scrolling behavior"""
        try:
            iterations = random.randint(*self.config.scroll_iterations_range)
            logger.info(f"🖱️ Simulating {iterations} scroll actions")
            
            for i in range(iterations):
                scroll_distance = random.randint(*self.config.scroll_distance_range)
                await self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                await asyncio.sleep(random.uniform(*self.config.sleep_scroll_range))
                logger.debug(f"  - Scroll {i+1}/{iterations}: {scroll_distance}px")
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error during scroll simulation",
                {"iterations": iterations, "config": self.config.scroll_iterations_range}
            )
            # Re-raise to allow caller to handle
            raise

    async def simulate_mouse_movements(self):
        """Simulate human-like mouse movements"""
        try:
            movements = random.randint(*self.config.mouse_movements_range)
            logger.info(f"🖱️ Simulating {movements} mouse movements")
            
            for i in range(movements):
                x = random.randint(100, 1000)
                y = random.randint(100, 800)
                steps = random.randint(5, 10)  # More steps = smoother movement
                await self.page.mouse.move(x, y, steps=steps)
                await asyncio.sleep(random.uniform(*self.config.sleep_mouse_range))
                logger.debug(f"  - Mouse move {i+1}/{movements}: to ({x}, {y})")
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error during mouse movement simulation",
                {"movements": movements, "config": self.config.mouse_movements_range}
            )
            # Re-raise to allow caller to handle
            raise

    async def simulate_user_behavior(self):
        """Simulate realistic user behavior combining scrolling and mouse movements"""
        try:
            logger.info("Starting human behavior simulation")
            await self.simulate_scrolling()
            await self.simulate_mouse_movements()
            
            # Add a small random delay to simulate reading
            reading_delay = random.uniform(0.5, 1.5)
            logger.debug(f"Simulating reading delay: {reading_delay:.2f}s")
            await asyncio.sleep(reading_delay)
            
            logger.info("Human behavior simulation completed")
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error during user behavior simulation",
                {"config": self.config.model_dump()}
            )
            # Re-raise to allow caller to handle
            raise 