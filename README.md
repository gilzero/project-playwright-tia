# TechInAsia Scraper Application

This is a web application built using FastAPI, Playwright, and Bootstrap 5 for scraping articles from the TechInAsia website. It allows users to specify various scraping parameters and view the results in a simple HTML table.

## Features

- **Web-Based Interface:** A user-friendly form for configuring scraping parameters.
- **Category-Specific Scraping:** Scrape articles based on a specified category (e.g., 'artificial-intelligence').
- **Configurable Parameters:**
    - Number of articles to scrape
    - Maximum page scrolls
    - Minimum and maximum delays between scrolls
- **Data Extraction:** Extracts article titles, source, posted time, categories, and tags.
- **Output:** Saves scraped data in batches as CSV files in the `output` directory.
- **Logging:** Logs all activity, including errors, in the `logs` directory.
- **Bootstrap 5 Styling:** Uses Bootstrap 5 for basic layout and styling.
- **Asynchronous Operations:** Uses Playwright's async API to make the scraping non-blocking
- **Retry Mechanism**: Implements retry mechanism when encountering error during page load.

## Project Structure

```
techinasia_app/
├── app/
│   ├── __init__.py      # Marks app as a python package
│   ├── api.py           # FastAPI endpoints and web application logic
│   ├── core.py          # Core scraping logic using Playwright
│   ├── models.py        # Pydantic models for data validation and configuration
│   ├── utils.py         # Utility functions for logging and output
│   ├── static/        # Static files (CSS)
│   │   └── css/
│   │       └── styles.css
│   └── templates/       # HTML templates
│       └── index.html     # Input form
│       └── results.html   # Display scraped data
├── logs/                # Log files
├── output/              # Output CSV files
├── main.py              # Main entry point to start the application
├── requirements.txt     # Python dependencies
└── pyproject.toml      # Python project configuration
```

## Getting Started

### Prerequisites

- Python 3.7+
- pip (Python package installer)

### Installation

1. Clone the repository:

    ```bash
    git clone <your_repository_url>
    cd techinasia_app
    ```
2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1. Navigate to the project directory:
   ```bash
   cd techinasia_app
   ```

2. Start the FastAPI application:
   ```bash
   python main.py
   ```

3. Open your web browser and go to `http://0.0.0.0:8000`

### Usage

1.  Fill out the form with your desired scraping parameters:
    - Number of Articles: The number of articles to scrape.
    - Max Scrolls:  The maximum number of scrolls for the scraping process.
    - Min Delay:  The minimum delay in seconds between scrolls.
    - Max Delay: The maximum delay in seconds between scrolls.
    - Category: The TechInAsia category you want to scrape (e.g., 'artificial-intelligence', 'fintech').
2.  Click the "Scrape Articles" button.
3.  Once complete, the table of scraped articles will be displayed on the page. The scraped data is also stored in CSV files in the `output` folder.

### Logs

All scraping activity is logged, with errors and warnings, in the `logs` directory.

### Output

The scraped article data is saved in batches as CSV files in the `output` directory.

## Further Development

-   Add better HTML result display.
-   Add input validation for the form.
-   Implement a database for storing the scraped results.
-   Implement more rate limiting logic.
-   Expand scraping capabilities to other TechInAsia content.
-   Add more error handling logic.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Versioning
v2.0.0 checkpointing

## jupyter notebook

- [test01.ipynb](./test01.ipynb)

description:

- web scraping system designed to fetch and process content from webpages. 
- It uses Playwright for browser automation, simulating human-like behavior such as scrolling and mouse movements to evade detection. 
- The Config class defines customizable parameters for user interaction simulation, timeouts, retries, and logging. 
- The asynchronous functions manage tasks like content extraction, retry mechanisms for failed requests, and processing a batch of URLs from a DataFrame. 
- Finally, the scraped data is saved to a JSON file with error handling to ensure reliability and robustness. This system is suitable for scalable and dynamic content extraction workflows.

