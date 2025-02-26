import asyncio
from app.scraper import TechInAsiaScraper
from app.models import ScraperConfig

async def main():
    # Create a simple configuration
    config = ScraperConfig(num_articles=1, max_scrolls=1)
    
    # Initialize and run the scraper
    scraper = TechInAsiaScraper(config)
    await scraper.scrape()
    
    print("Scraping completed.")

if __name__ == "__main__":
    asyncio.run(main()) 