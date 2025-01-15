# main.py
import uvicorn
from app.api import app
from app.utils import setup_logging

logger = setup_logging()

if __name__ == "__main__":
    logger.info("Starting FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")