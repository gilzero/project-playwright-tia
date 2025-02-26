# app/core.py
from app.scraper import TechInAsiaScraper
from app.human_behavior import HumanBehaviorSimulator
from app.models import ScraperConfig
from app.logger import get_logger, log_exception, log_summary

# This file now serves as a simple re-export of the main components
# The functionality has been modularized into separate files:
# - app/human_behavior.py: Contains the HumanBehaviorSimulator class
# - app/scraper.py: Contains the TechInAsiaScraper class
# - app/logger.py: Contains the centralized logging functionality

__all__ = [
    'TechInAsiaScraper', 
    'HumanBehaviorSimulator', 
    'ScraperConfig',
    'get_logger',
    'log_exception',
    'log_summary'
]