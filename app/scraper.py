# app/scraper.py
"""
This module is kept for backward compatibility.
The actual implementation has been refactored into the app/scraper/ package.
"""

from app.scraper.main import TechInAsiaScraper
from app.models import Article, ScraperConfig

# Re-export the main class for backward compatibility
__all__ = ['TechInAsiaScraper', 'Article', 'ScraperConfig'] 