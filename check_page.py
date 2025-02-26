#!/usr/bin/env python
# check_page.py

from playwright.sync_api import sync_playwright
import time
import os

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Navigate to the page
        print("Navigating to TechInAsia...")
        page.goto('https://www.techinasia.com/news?category=startups', timeout=60000)
        
        # Wait for the page to load
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Scroll down a few times to load more content
        print("Scrolling down to load more content...")
        for i in range(3):
            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(1)
        
        # Get the HTML content
        html = page.content()
        
        # Save the HTML to a file
        with open('current_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Take a screenshot
        page.screenshot(path="techinasia_screenshot.png")
        
        # Print some debug info
        article_elements = page.query_selector_all('article')
        print(f"Found {len(article_elements)} article elements")
        
        # Try different selectors
        selectors = [
            'article', 
            '.post-card', 
            '.article', 
            '.news-item',
            'div[class*="post"]',
            'div[class*="article"]'
        ]
        
        for selector in selectors:
            elements = page.query_selector_all(selector)
            print(f"Selector '{selector}': {len(elements)} elements found")
            
            # If elements found, print the first one's HTML
            if elements and len(elements) > 0:
                print(f"First element HTML for '{selector}':")
                html = elements[0].evaluate("el => el.outerHTML")
                print(html[:200] + "..." if len(html) > 200 else html)
                print("-" * 50)
        
        browser.close()
        
        print("Page content saved to current_page.html")
        print("Screenshot saved to techinasia_screenshot.png")

if __name__ == "__main__":
    main() 