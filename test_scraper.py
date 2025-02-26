#!/usr/bin/env python
# test_scraper.py

import os
import sys
import asyncio
import argparse
from datetime import datetime
from playwright.async_api import async_playwright

from app.models import ScraperConfig
from app.core import TechInAsiaScraper
from app.logger import setup_logging, log_summary
from app.utils import save_articles_to_json, save_articles_to_csv

async def test_scraper(config):
    """Test the scraper with the given configuration."""
    logger = setup_logging(log_dir=os.path.dirname(config.log_file), log_level=config.log_level)
    logger.info(f"Starting test scraper with configuration: {config.model_dump()}")
    
    # Start timing
    start_time = datetime.now()
    logger.info(f"Scraping started at {start_time}")
    
    try:
        # Initialize the scraper and browser
        async with async_playwright() as playwright:
            # Initialize the scraper
            scraper = TechInAsiaScraper(config)
            
            # Initialize the browser
            await scraper.setup_browser(playwright)
            
            # Scrape the article list
            articles = await scraper.scrape_article_list()
            
            # End timing
            end_time = datetime.now()
            
            # Log summary
            log_summary(
                total_articles=len(articles),
                processed_ids=scraper.processed_article_ids,
                incomplete_articles=scraper.incomplete_articles,
                start_time=start_time,
                end_time=end_time,
                config=config.model_dump()
            )
            
            # Save results
            if articles:
                # Create output directory if it doesn't exist
                os.makedirs(config.output_dir, exist_ok=True)
                
                # Generate filenames
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = os.path.join(config.output_dir, f"techinasia_{config.category}_{timestamp}.csv")
                json_filename = os.path.join(config.output_dir, f"techinasia_{config.category}_{timestamp}.json")
                
                # Save to CSV and JSON
                save_articles_to_csv(articles, csv_filename)
                save_articles_to_json(articles, json_filename)
                
                logger.info(f"Test completed successfully. Scraped {len(articles)} articles.")
                return articles
            else:
                logger.warning("No articles were scraped during the test.")
                return []
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        raise

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the TechInAsia scraper")
    parser.add_argument("--num-articles", type=int, default=5, help="Number of articles to scrape")
    parser.add_argument("--max-scrolls", type=int, default=3, help="Maximum number of scrolls")
    parser.add_argument("--category", type=str, default="startups", help="Category to scrape")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    parser.add_argument("--extract-content", action="store_true", help="Extract full article content")
    parser.add_argument("--randomize-user-agent", action="store_true", help="Randomize user agent")
    parser.add_argument("--randomize-viewport", action="store_true", help="Randomize viewport size")
    return parser.parse_args()

async def main():
    """Main entry point for the test script."""
    args = parse_args()
    
    # Create configuration
    config = ScraperConfig(
        num_articles=args.num_articles,
        max_scrolls=args.max_scrolls,
        category=args.category,
        output_dir=args.output_dir,
        log_file="logs/test_scraper.log",
        log_level=args.log_level,
        extract_content=args.extract_content,
        randomize_user_agent=args.randomize_user_agent,
        randomize_viewport=args.randomize_viewport
    )
    
    # Run the test
    await test_scraper(config)

if __name__ == "__main__":
    asyncio.run(main()) 