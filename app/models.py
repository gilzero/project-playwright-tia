# app/models.py
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from dateutil import parser
import logging

logger = logging.getLogger(__name__)
class Article(BaseModel):
    """Data class for storing article information"""
    article_id: Optional[str] = None
    title: str = 'N/A'
    article_url: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    posted_time: Optional[str] = None
    relative_time: str = 'N/A'
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    scraped_at: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    posted_time_iso: Optional[str] = None

    @field_validator('article_url', 'source_url', 'image_url', mode='before')
    def validate_urls(cls, v):
        """Validate and clean URLs"""
        if v == 'N/A':
            return None
        return v

    @field_validator('posted_time_iso', mode='before')
    def convert_posted_time(cls, v, values):
        posted_time = values.data.get('posted_time')
        if posted_time:
            try:
                dt = parser.parse(posted_time)
                return dt.isoformat()
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse posted_time: {posted_time}, error: {e}")
        return None

    def model_dump_json(self) -> str:
        """Convert the Article instance to a JSON string"""
        return self.model_dump_json()


class ScraperConfig(BaseModel):
    """Configuration management for the scraper"""
    num_articles: int = 50
    max_scrolls: int = 10
    timeout: int = 20
    retry_count: int = 3
    scroll_pause_time: float = 1.5
    batch_size: int = 100
    base_url: str = 'https://www.techinasia.com/news'
    output_dir: str = 'output'
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    min_delay: float = 1
    max_delay: float = 3
    category: str = 'artificial-intelligence'

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True
    )

    @field_validator('num_articles', 'max_scrolls', 'timeout', 'retry_count', 'batch_size')
    def validate_positive_int(cls, v: int) -> int:
        if not isinstance(v, int) or v <= 0:
            raise ValueError(f"{cls.__name__} must be a positive integer")
        return v

    @field_validator('scroll_pause_time', 'min_delay', 'max_delay')
    def validate_positive_number(cls, v: float) -> float:
        if not isinstance(v, (int, float)) or v <= 0:
            raise ValueError(f"{cls.__name__} must be a positive number")
        return v

    @field_validator('max_delay')
    def validate_max_delay(cls, v: float, info) -> float:
        if 'min_delay' in info.data and v < info.data['min_delay']:
            raise ValueError("max_delay must be greater than or equal to min_delay")
        return v

    @field_validator('category')
    def validate_non_empty_string(cls, v: str) -> str:
        if not isinstance(v, str) or not v:
            raise ValueError("category must be a non-empty string")
        return v