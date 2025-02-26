# app/models.py
from typing import List, Optional, Tuple, Dict, Any
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
    content: Optional[str] = None
    scraped_at: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


    @field_validator('article_url', 'source_url', 'image_url', mode='before')
    def validate_urls(cls, v):
        """Validate and clean URLs"""
        if v == 'N/A':
            return None
        return v

    def model_dump_json(self) -> str:
        """Convert the Article instance to a JSON string"""
        return self.model_dump_json()


class ScraperConfig(BaseModel):
    """Enhanced configuration management for the scraper with human-like behavior simulation"""
    # Basic scraping parameters
    num_articles: int = 50
    max_scrolls: int = 10
    timeout: int = 20000  # in milliseconds
    retry_count: int = 5
    batch_size: int = 100
    base_url: str = 'https://www.techinasia.com/news'
    output_dir: str = 'output'
    category: str = 'artificial-intelligence'
    filename_prefix: str = 'techinasia_ai_news'
    
    # Human-like behavior simulation parameters
    scroll_iterations_range: Tuple[int, int] = (1, 3)
    scroll_distance_range: Tuple[int, int] = (50, 200)
    mouse_movements_range: Tuple[int, int] = (1, 3)
    sleep_scroll_range: Tuple[float, float] = (0.1, 0.5)
    sleep_mouse_range: Tuple[float, float] = (0.1, 0.3)
    url_delay_range: Tuple[float, float] = (1.0, 3.0)
    
    # Randomization parameters
    randomize_user_agent: bool = True
    randomize_viewport: bool = True
    
    # User agents and viewport sizes for randomization
    user_agents: List[str] = Field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.18",
        "Safari/537.36 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
        "Edge/91.0.864.59 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    ])
    
    viewport_sizes: List[Dict[str, int]] = Field(default_factory=lambda: [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1280, "height": 720},
        {"width": 1440, "height": 900},
        {"width": 1280, "height": 1024},
        {"width": 1024, "height": 768},
        {"width": 1600, "height": 900},
        {"width": 1680, "height": 1050},
    ])
    
    # Content selectors with fallbacks
    content_selectors: List[str] = Field(default_factory=lambda: [
        "div#content.content",
        "div.jsx-3810287742.jsx-430771670.content",
        "article.content",
        "div.article-content",
        "div.article-body",
        "div.story-content",
        "div.story-body",
        "div.post-content",
        "div.entry-content",
        "main article",
        "main .content",
        "article .content",
        ".article__body",
        ".article__content",
        ".post__content",
        ".post-body",
    ])
    
    # Logging configuration
    log_file: str = "logs/scraper.log"
    log_level: str = "INFO"

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True
    )

    @field_validator('num_articles', 'max_scrolls', 'retry_count', 'batch_size')
    def validate_positive_int(cls, v: int) -> int:
        if not isinstance(v, int) or v <= 0:
            raise ValueError(f"Value must be a positive integer")
        return v

    @field_validator('scroll_iterations_range', 'scroll_distance_range', 'mouse_movements_range')
    def validate_int_range(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        if not isinstance(v, tuple) or len(v) != 2 or not all(isinstance(x, int) for x in v):
            raise ValueError("Range must be a tuple of two integers")
        if v[0] > v[1]:
            raise ValueError("First value in range must be less than or equal to second value")
        if v[0] <= 0:
            raise ValueError("Range values must be positive")
        return v

    @field_validator('sleep_scroll_range', 'sleep_mouse_range', 'url_delay_range')
    def validate_float_range(cls, v: Tuple[float, float]) -> Tuple[float, float]:
        if not isinstance(v, tuple) or len(v) != 2 or not all(isinstance(x, (int, float)) for x in v):
            raise ValueError("Range must be a tuple of two numbers")
        if v[0] > v[1]:
            raise ValueError("First value in range must be less than or equal to second value")
        if v[0] < 0:
            raise ValueError("Range values must be non-negative")
        return v

    @field_validator('user_agents', 'viewport_sizes', 'content_selectors')
    def validate_non_empty_list(cls, v: List[Any]) -> List[Any]:
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError("Must be a non-empty list")
        return v

    @field_validator('category')
    def validate_non_empty_string(cls, v: str) -> str:
        if not isinstance(v, str) or not v:
            raise ValueError("category must be a non-empty string")
        return v