# tests/test_parser.py
import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import os
import sys
import json

from app.models import ScraperConfig, Article
from app.scraper.parser import ArticleParser

class TestArticleParser(unittest.TestCase):
    """Test cases for the ArticleParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ScraperConfig(
            category="artificial-intelligence",
            base_url="https://www.techinasia.com/news"
        )
        self.parser = ArticleParser(self.config)
        
        # Sample HTML for testing
        self.sample_html = """
        <article class="post-card">
            <div class="post-content">
                <h3 class="post-title"><a href="/some-article-path">Test Article Title</a></h3>
                <span class="post-source-name">Test Source</span>
                <a class="post-source" href="/source-link">Source Link</a>
                <time datetime="2023-01-01T12:00:00Z">1 day ago</time>
                <a class="category-link" href="/category/ai">AI</a>
                <a class="tag-link" href="/tag/machine-learning">Machine Learning</a>
            </div>
            <div class="post-image">
                <img src="https://example.com/image.jpg" alt="Test Image">
            </div>
        </article>
        """
        self.soup = BeautifulSoup(self.sample_html, 'html.parser')
        self.article_element = self.soup.find('article')
    
    def test_parse_article(self):
        """Test parsing an article from HTML."""
        article = self.parser.parse_article(self.article_element)
        
        self.assertIsNotNone(article)
        self.assertEqual(article.title, "Test Article Title")
        self.assertEqual(article.article_url, "https://www.techinasia.com/some-article-path")
        self.assertEqual(article.source, "Test Source")
        self.assertEqual(article.source_url, "https://www.techinasia.com/source-link")
        self.assertEqual(article.image_url, "https://example.com/image.jpg")
        self.assertEqual(article.relative_time, "1 day ago")
        self.assertIn("AI", article.categories)
        self.assertIn("Machine Learning", article.tags)
    
    def test_extract_article_id_and_url(self):
        """Test extracting article ID and URL."""
        content_div = self.article_element.find('div', class_='post-content')
        article_id, article_url = self.parser._extract_article_id_and_url(content_div)
        
        self.assertEqual(article_id, "some-article-path")
        self.assertEqual(article_url, "https://www.techinasia.com/some-article-path")
    
    def test_extract_title(self):
        """Test extracting article title."""
        content_div = self.article_element.find('div', class_='post-content')
        title = self.parser._extract_title(content_div)
        
        self.assertEqual(title, "Test Article Title")
    
    def test_extract_source_info(self):
        """Test extracting source information."""
        content_div = self.article_element.find('div', class_='post-content')
        source, source_url = self.parser._extract_source_info(content_div)
        
        self.assertEqual(source, "Test Source")
        self.assertEqual(source_url, "https://www.techinasia.com/source-link")
    
    def test_extract_image_url(self):
        """Test extracting image URL."""
        image_url = self.parser._extract_image_url(self.article_element)
        
        self.assertEqual(image_url, "https://example.com/image.jpg")
    
    def test_extract_time_info(self):
        """Test extracting time information."""
        posted_time, relative_time = self.parser._extract_time_info(self.article_element)
        
        self.assertIsNotNone(posted_time)  # The exact format might vary
        self.assertEqual(relative_time, "1 day ago")
    
    def test_extract_categories_and_tags(self):
        """Test extracting categories and tags."""
        categories, tags = self.parser._extract_categories_and_tags(self.article_element)
        
        self.assertIn("AI", categories)
        self.assertIn("Machine Learning", tags)
    
    def test_is_valid_article(self):
        """Test article validation."""
        valid_article = Article(
            article_id="test-id",
            title="Test Title",
            article_url="https://example.com/test"
        )
        invalid_article = Article(
            article_id="test-id",
            title="Test Title",
            article_url=None
        )
        
        self.assertTrue(self.parser.is_valid_article(valid_article))
        self.assertFalse(self.parser.is_valid_article(invalid_article))

if __name__ == '__main__':
    unittest.main() 