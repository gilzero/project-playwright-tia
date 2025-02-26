# main.py
import os
import uvicorn
import argparse
from app.api import app
from app.utils import setup_logging
from app.models import ScraperConfig

def parse_arguments():
    """Parse command line arguments for the application."""
    parser = argparse.ArgumentParser(description="TechInAsia Scraper API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the API on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the API on")
    parser.add_argument("--log-level", type=str, default="info", 
                        choices=["debug", "info", "warning", "error", "critical"],
                        help="Logging level")
    parser.add_argument("--output-dir", type=str, default="output", 
                        help="Directory to store output files")
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Setup logging
    log_file = os.path.join("logs", "app.log")
    logger = setup_logging(log_file=log_file, log_level=args.log_level.upper())
    
    # Create default config for the app context
    default_config = ScraperConfig(
        num_articles=10,
        max_scrolls=5,
        category="startups",
        output_dir=args.output_dir,
        log_file=log_file,
        log_level=args.log_level.upper()
    )
    
    # Store default config in app state
    app.state.default_config = default_config
    
    # Log startup information
    logger.info(f"Starting TechInAsia Scraper API on {args.host}:{args.port}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Log level: {args.log_level}")
    
    # Start the server
    uvicorn.run(
        app, 
        host=args.host, 
        port=args.port, 
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()