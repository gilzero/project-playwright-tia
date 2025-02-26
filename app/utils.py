# app/utils.py
import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.logger import get_logger, log_exception

# Get the logger instance
logger = get_logger()

def setup_output_directory(output_dir: str) -> str:
    """
    Create output directory if it doesn't exist and return the absolute path.
    
    Args:
        output_dir: Path to the output directory
        
    Returns:
        Absolute path to the output directory
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        
        abs_path = os.path.abspath(output_dir)
        logger.debug(f"Output directory path: {abs_path}")
        return abs_path
    except Exception as e:
        log_exception(
            logger, 
            e, 
            f"Failed to create output directory: {output_dir}",
            {'output_dir': output_dir}
        )
        raise


def save_articles_to_csv(articles: List[Dict[Any, Any]], output_path: str) -> str:
    """
    Save articles to a CSV file.
    
    Args:
        articles: List of article dictionaries
        output_path: Path to save the CSV file
        
    Returns:
        Path to the saved CSV file
    """
    try:
        df = pd.DataFrame(articles)
        
        # Convert list fields to strings for CSV compatibility
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, list)).any():
                df[col] = df[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"✅ Saved {len(articles)} articles to CSV: {output_path}")
        return output_path
    except Exception as e:
        log_exception(
            logger, 
            e, 
            f"Error saving articles to CSV: {output_path}",
            {'article_count': len(articles), 'output_path': output_path}
        )
        raise


def save_articles_to_json(articles: List[Dict[Any, Any]], output_path: str) -> str:
    """
    Save articles to a JSON file.
    
    Args:
        articles: List of article dictionaries
        output_path: Path to save the JSON file
        
    Returns:
        Path to the saved JSON file
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert Article objects to dictionaries if needed
        articles_dicts = []
        for article in articles:
            if hasattr(article, 'model_dump'):
                # If it's a Pydantic model
                articles_dicts.append(article.model_dump())
            elif hasattr(article, '__dict__'):
                # If it's a regular class instance
                articles_dicts.append(article.__dict__)
            else:
                # If it's already a dictionary
                articles_dicts.append(article)
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles_dicts, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✅ Saved {len(articles)} articles to JSON: {output_path}")
        return output_path
    except Exception as e:
        log_exception(
            logger, 
            e, 
            f"Error saving articles to JSON: {output_path}",
            {'article_count': len(articles), 'output_path': output_path}
        )
        raise


def truncate_text(text: str, max_length: int = 150) -> str:
    """
    Truncate text to a maximum length and add ellipsis if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the truncated text
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
        
    if len(text) <= max_length:
        return text
        
    return text[:max_length].rstrip() + "..."


def generate_filename(prefix: str, category: str = None, extension: str = "csv") -> str:
    """
    Generate a filename with timestamp and optional category.
    
    Args:
        prefix: Prefix for the filename
        category: Category to include in the filename (optional)
        extension: File extension (default: csv)
        
    Returns:
        Generated filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if category:
        return f"{prefix}_{category}_{timestamp}.{extension}"
    return f"{prefix}_{timestamp}.{extension}"

# Note: The old setup_logging and log_summary functions have been removed
# as they are now in the centralized logger.py module