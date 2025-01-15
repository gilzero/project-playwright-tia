# app/utils.py
import os
import logging
from datetime import datetime

def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def log_summary(logger, total_articles, processed_ids, incomplete_articles, start_time, end_time):
    """Log summary statistics of the scraping process"""
    duration = end_time - start_time
    logger.info("📊 --- Scraping Summary ---")
    logger.info(f"📰 Total articles scraped: {total_articles}")
    logger.info(f"✅ Valid articles scraped: {len(processed_ids)}")
    logger.info(f"⚠️ Incomplete articles skipped: {incomplete_articles}")
    logger.info(f"🔄 Duplicate articles skipped: {total_articles - len(processed_ids) - incomplete_articles}")
    logger.info(f"⏱️ Scraping duration: {duration}")
    logger.info("📊 ------------------------")