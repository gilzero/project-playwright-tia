# app/scraper/storage.py
import os
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from app.models import Article, ScraperConfig
from app.logger import get_logger, log_exception
from app.utils import save_articles_to_csv, save_articles_to_json

# Get the logger instance
logger = get_logger()

class StorageManager:
    """Manages storage of scraped articles"""
    def __init__(self, config: ScraperConfig):
        """Initialize the storage manager with configuration"""
        self.config = config
        logger.info(f"Initialized StorageManager with output directory: {self.config.output_dir}")

    def save_to_csv(self, articles: List[Article]) -> str:
        """Save articles to a CSV file"""
        if not articles:
            logger.warning("⚠️ No articles to save")
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_num = 0  # You could implement batch numbering if needed
        filename = f"{self.config.filename_prefix}_batch_{batch_num}_{timestamp}.csv"
        filepath = os.path.join(self.config.output_dir, filename)
        
        try:
            # Convert articles to DataFrame
            articles_dict = [article.model_dump() for article in articles]
            return save_articles_to_csv(articles_dict, filepath)
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error saving articles to CSV",
                {"article_count": len(articles), "filepath": filepath}
            )
            return ""

    def save_to_json(self, articles: List[Article]) -> str:
        """Save articles to a JSON file"""
        if not articles:
            logger.warning("⚠️ No articles to save")
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_num = 0  # You could implement batch numbering if needed
        filename = f"{self.config.filename_prefix}_batch_{batch_num}_{timestamp}.json"
        filepath = os.path.join(self.config.output_dir, filename)
        
        try:
            # Convert articles to dict
            articles_dict = [article.model_dump() for article in articles]
            return save_articles_to_json(articles_dict, filepath)
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error saving articles to JSON",
                {"article_count": len(articles), "filepath": filepath}
            )
            return ""
            
    def to_dataframe(self, articles: List[Article]) -> pd.DataFrame:
        """Convert articles to a pandas DataFrame"""
        if not articles:
            logger.warning("⚠️ No articles to convert to DataFrame")
            return pd.DataFrame()
            
        try:
            # Convert articles to dict
            articles_dict = [article.model_dump() for article in articles]
            return pd.DataFrame(articles_dict)
        except Exception as e:
            log_exception(
                logger,
                e,
                "Error converting articles to DataFrame",
                {"article_count": len(articles)}
            )
            return pd.DataFrame()
