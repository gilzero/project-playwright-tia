 # app/api.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.core import TechInAsiaScraper
from app.models import ScraperConfig, Article
import pandas as pd

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class ScrapeRequest(BaseModel):
    num_articles: int = 50
    max_scrolls: int = 10
    min_delay: float = 1.0
    max_delay: float = 3.0
    category: str = 'artificial-intelligence'

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    """Serve the HTML form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scrape", response_class=HTMLResponse)
async def scrape_articles(request: Request, scrape_request: ScrapeRequest):
    """Handle scraping and display results."""
    try:
        config = ScraperConfig(**scrape_request.model_dump())
        scraper = TechInAsiaScraper(config=config)
        df = await scraper.scrape()

        if not df.empty:
            # Dynamically generate display columns based on Article model fields
            display_columns = [field for field in Article.model_fields.keys() if field in df.columns]
            return templates.TemplateResponse("results.html", {"request": request, "articles": df[display_columns].to_dict('records')})
        else:
            return templates.TemplateResponse("results.html", {"request": request, "message": "No articles found with this search query."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))