# app/api.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from app.core import TechInAsiaScraper, get_logger, log_exception
from app.models import ScraperConfig, Article
import pandas as pd
from datetime import datetime

# Get the logger instance
logger = get_logger()

app = FastAPI(title="TechInAsia Scraper API", 
              description="Advanced web scraper for TechInAsia with human-like behavior simulation",
              version="2.0.0")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Log application startup
logger.info("🚀 TechInAsia Scraper API starting up")

@app.on_event("startup")
async def startup_event():
    """Log when the application starts"""
    logger.info(f"✅ API server started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📚 API documentation available at /docs and /redoc")

@app.on_event("shutdown")
async def shutdown_event():
    """Log when the application shuts down"""
    logger.info(f"🛑 API server shutting down at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

class ScrapeRequest(BaseModel):
    """Request model for scraping configuration"""
    # Basic scraping parameters
    num_articles: int = Field(50, description="Number of articles to scrape", ge=1, le=200)
    max_scrolls: int = Field(10, description="Maximum number of page scrolls", ge=1, le=50)
    category: str = Field('artificial-intelligence', description="Category to scrape (e.g., 'artificial-intelligence', 'fintech')")
    
    # Human-like behavior simulation parameters
    scroll_iterations_min: int = Field(1, description="Minimum number of scroll iterations per page", ge=1, le=10)
    scroll_iterations_max: int = Field(3, description="Maximum number of scroll iterations per page", ge=1, le=10)
    
    scroll_distance_min: int = Field(50, description="Minimum scroll distance in pixels", ge=10, le=500)
    scroll_distance_max: int = Field(200, description="Maximum scroll distance in pixels", ge=10, le=500)
    
    sleep_scroll_min: float = Field(0.1, description="Minimum sleep time after scrolling (seconds)", ge=0.1, le=2.0)
    sleep_scroll_max: float = Field(0.5, description="Maximum sleep time after scrolling (seconds)", ge=0.1, le=2.0)
    
    url_delay_min: float = Field(0.5, description="Minimum delay between URL requests (seconds)", ge=0.1, le=5.0)
    url_delay_max: float = Field(2.0, description="Maximum delay between URL requests (seconds)", ge=0.1, le=5.0)
    
    # Randomization options
    randomize_user_agent: bool = Field(True, description="Randomize user agent for each request")
    randomize_viewport: bool = Field(True, description="Randomize viewport size for each request")
    
    # Output options
    save_content: bool = Field(True, description="Extract and save full article content")

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    """Serve the HTML form"""
    logger.info("Serving main form page")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scrape", response_class=HTMLResponse)
async def scrape_articles(request: Request, scrape_request: ScrapeRequest):
    """Handle scraping and display results."""
    start_time = datetime.now()
    logger.info(f"Web UI scrape request received for category: {scrape_request.category}")
    logger.debug(f"Scrape request parameters: {scrape_request.model_dump_json()}")
    
    try:
        # Convert the ScrapeRequest to ScraperConfig
        config_dict = {
            "num_articles": scrape_request.num_articles,
            "max_scrolls": scrape_request.max_scrolls,
            "category": scrape_request.category,
            "scroll_iterations_range": (scrape_request.scroll_iterations_min, scrape_request.scroll_iterations_max),
            "scroll_distance_range": (scrape_request.scroll_distance_min, scrape_request.scroll_distance_max),
            "sleep_scroll_range": (scrape_request.sleep_scroll_min, scrape_request.sleep_scroll_max),
            "url_delay_range": (scrape_request.url_delay_min, scrape_request.url_delay_max),
            "randomize_user_agent": scrape_request.randomize_user_agent,
            "randomize_viewport": scrape_request.randomize_viewport,
        }
        
        config = ScraperConfig(**config_dict)
        logger.info(f"Starting scraper with config for category: {config.category}")
        
        scraper = TechInAsiaScraper(config=config)
        df = await scraper.scrape()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if not df.empty:
            # Dynamically generate display columns based on Article model fields
            display_columns = [field for field in Article.model_fields.keys() 
                              if field in df.columns and field not in ['content']]
            
            # Truncate content for display if it exists
            if 'content' in df.columns and not df['content'].isna().all():
                df['content_preview'] = df['content'].apply(
                    lambda x: f"{x[:150]}..." if x and len(x) > 150 else x
                )
                display_columns.append('content_preview')
            
            logger.info(f"Web UI scrape completed successfully: {len(df)} articles found in {duration:.2f} seconds")
            return templates.TemplateResponse(
                "results.html", 
                {
                    "request": request, 
                    "articles": df[display_columns].to_dict('records'),
                    "total_articles": len(df),
                    "config": config_dict
                }
            )
        else:
            logger.warning(f"Web UI scrape completed with no results in {duration:.2f} seconds")
            return templates.TemplateResponse(
                "results.html", 
                {
                    "request": request, 
                    "message": "No articles found with this search query.",
                    "config": config_dict
                }
            )
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        log_exception(
            logger,
            e,
            f"Error during web UI scrape",
            {
                "category": scrape_request.category,
                "duration": duration,
                "request": scrape_request.model_dump()
            }
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape", response_class=JSONResponse)
async def api_scrape_articles(scrape_request: ScrapeRequest):
    """API endpoint for scraping articles and returning JSON data."""
    start_time = datetime.now()
    logger.info(f"API scrape request received for category: {scrape_request.category}")
    logger.debug(f"API scrape request parameters: {scrape_request.model_dump_json()}")
    
    try:
        # Convert the ScrapeRequest to ScraperConfig
        config_dict = {
            "num_articles": scrape_request.num_articles,
            "max_scrolls": scrape_request.max_scrolls,
            "category": scrape_request.category,
            "scroll_iterations_range": (scrape_request.scroll_iterations_min, scrape_request.scroll_iterations_max),
            "scroll_distance_range": (scrape_request.scroll_distance_min, scrape_request.scroll_distance_max),
            "sleep_scroll_range": (scrape_request.sleep_scroll_min, scrape_request.sleep_scroll_max),
            "url_delay_range": (scrape_request.url_delay_min, scrape_request.url_delay_max),
            "randomize_user_agent": scrape_request.randomize_user_agent,
            "randomize_viewport": scrape_request.randomize_viewport,
        }
        
        config = ScraperConfig(**config_dict)
        logger.info(f"Starting API scraper with config for category: {config.category}")
        
        scraper = TechInAsiaScraper(config=config)
        df = await scraper.scrape()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if not df.empty:
            # Convert DataFrame to list of dictionaries
            articles = df.to_dict('records')
            logger.info(f"API scrape completed successfully: {len(articles)} articles found in {duration:.2f} seconds")
            return {"status": "success", "articles": articles, "count": len(articles), "duration_seconds": duration}
        else:
            logger.warning(f"API scrape completed with no results in {duration:.2f} seconds")
            return {"status": "success", "articles": [], "count": 0, "message": "No articles found", "duration_seconds": duration}
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        log_exception(
            logger,
            e,
            f"Error during API scrape",
            {
                "category": scrape_request.category,
                "duration": duration,
                "request": scrape_request.model_dump()
            }
        )
        return {"status": "error", "message": str(e), "duration_seconds": duration}