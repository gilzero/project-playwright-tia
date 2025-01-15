 # app/api.py
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional
from app.core import TechInAsiaScraper
from app.models import ScraperConfig
import pandas as pd

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    """Serve the HTML form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scrape", response_class=HTMLResponse)
async def scrape_articles(
        request: Request,
        num_articles: int = Form(50),
        max_scrolls: int = Form(10),
        min_delay: float = Form(1),
        max_delay: float = Form(3),
        category: str = Form('artificial-intelligence')
):
    """Handle scraping and display results."""
    try:
        config_data = {
            'num_articles': num_articles,
            'max_scrolls': max_scrolls,
            'min_delay': min_delay,
            'max_delay': max_delay,
            'category': category
        }
        config = ScraperConfig(**config_data)
        scraper = TechInAsiaScraper(config=config)
        df = await scraper.scrape()

        if not df.empty:
            display_columns = ['title', 'source', 'posted_time_iso', 'categories', 'tags']
            return templates.TemplateResponse("results.html", {"request": request, "articles": df[display_columns].to_dict('records')})
        else:
            return templates.TemplateResponse("results.html", {"request": request, "message": "No articles found with this search query."})
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))