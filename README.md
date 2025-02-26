# TechInAsia Scraper Application

This is a web application built using FastAPI, Playwright, and Bootstrap 5 for scraping articles from the TechInAsia website. It allows users to specify various scraping parameters and view the results in a simple HTML table.

## Features

- **Web-Based Interface:** A user-friendly form for configuring scraping parameters.
- **Category-Specific Scraping:** Scrape articles based on a specified category (e.g., 'artificial-intelligence').
- **Advanced Human-Like Behavior Simulation:**
  - Randomized scrolling patterns
  - Simulated mouse movements
  - Variable sleep times between actions
  - Randomized user agents and viewport sizes
- **Configurable Parameters:**
  - Number of articles to scrape
  - Maximum page scrolls
  - Scroll iterations and distances
  - Sleep durations between actions
  - URL request delays
- **Data Extraction:** Extracts article titles, source, posted time, categories, tags, and content.
- **Output Options:** 
  - Save scraped data as CSV and JSON files
  - Preview content in the web interface
  - Export results directly from the browser
- **Detailed Article View:** Modal popup with complete article details
- **Logging:** Comprehensive logging with configurable levels in the `logs` directory.
- **Bootstrap 5 Styling:** Modern responsive UI with Bootstrap 5.
- **Asynchronous Operations:** Uses Playwright's async API for non-blocking scraping.
- **Robust Error Handling:** Implements retry mechanisms with exponential backoff.

## Project Structure

```
project-playwright-tia/
├── app/
│   ├── __init__.py      # Marks app as a python package
│   ├── api.py           # FastAPI endpoints and web application logic
│   ├── core.py          # Core scraping logic using Playwright
│   ├── models.py        # Pydantic models for data validation and configuration
│   ├── utils.py         # Utility functions for logging and output
│   ├── static/          # Static files (CSS)
│   │   └── css/
│   │       └── styles.css
│   └── templates/       # HTML templates
│       ├── index.html   # Input form with advanced options
│       └── results.html # Enhanced results display with content preview
├── logs/                # Log files
├── output/              # Output CSV and JSON files
├── main.py              # Main entry point with command-line options
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.7+
- pip (Python package installer)

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/project-playwright-tia.git
    cd project-playwright-tia
    ```

2. Create and activate a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Install Playwright browsers:
    ```bash
    playwright install
    ```

### Running the Application

1. Start the FastAPI application:
   ```bash
   python main.py
   ```

2. For additional configuration options:
   ```bash
   python main.py --host 127.0.0.1 --port 8080 --log-level debug --output-dir custom_output
   ```

3. Open your web browser and go to `http://localhost:8000` (or the host/port you specified)

### Usage

1. Fill out the form with your desired scraping parameters:

   **Basic Scraping Parameters:**
   - Number of Articles: The number of articles to scrape
   - Max Scrolls: The maximum number of scrolls for the scraping process
   - Category: The TechInAsia category you want to scrape (e.g., 'startups', 'artificial-intelligence')

   **Human-like Behavior Simulation:**
   - Scroll Iterations Range: Number of scroll iterations per scroll action
   - Scroll Distance Range: Pixel distance for each scroll action
   - Sleep After Scroll Range: Seconds to wait after scrolling
   - URL Request Delay Range: Seconds to wait between URL requests

   **Randomization Options:**
   - Randomize User Agent: Use different browser user agents
   - Randomize Viewport Size: Use different browser window sizes

   **Output Options:**
   - Extract Full Content: Scrape the full article content (slower)

2. Click the "Start Scraping" button.

3. Once complete, the results page will display:
   - A summary of the scraping configuration
   - A table of scraped articles with content previews
   - Options to view detailed article information
   - Export functionality to download results as CSV

### Command Line Options

The application supports the following command-line options:

```bash
python main.py --help
```

- `--host`: Host to run the API on (default: 0.0.0.0)
- `--port`: Port to run the API on (default: 8000)
- `--log-level`: Logging level (choices: debug, info, warning, error, critical; default: info)
- `--output-dir`: Directory to store output files (default: output)

### Logs

All scraping activity is logged in the `logs` directory. The log level can be configured via command-line arguments or in the configuration.

### Output

The scraped article data is saved as both CSV and JSON files in the `output` directory. The filename includes the category and timestamp.

## Advanced Features

### Human-Like Behavior Simulation

The scraper implements advanced techniques to simulate human-like behavior:

- **Variable Scrolling Patterns:** Randomizes the number of scrolls and scroll distances
- **Mouse Movement Simulation:** Moves the mouse cursor in random patterns
- **Sleep Timing Variation:** Adds random delays between actions
- **User Agent Rotation:** Cycles through different browser user agents
- **Viewport Size Randomization:** Changes browser window dimensions

### Error Handling and Retries

The application implements robust error handling:

- **Exponential Backoff:** Increases wait time between retry attempts
- **Configurable Retry Attempts:** Set maximum number of retries
- **Detailed Error Logging:** Captures and logs all exceptions

## Further Development

- Add authentication for API access
- Implement a database for storing the scraped results
- Add proxy support for distributed scraping
- Implement scheduled scraping jobs
- Add support for additional websites
- Create a Docker container for easy deployment

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Version History

- v3.0.0: Enhanced scraper with human-like behavior simulation and advanced configuration
- v2.0.0: Added basic web interface and improved scraping logic
- v1.0.0: Initial release with core scraping functionality

## jupyter notebook

- [test01.ipynb](./test01.ipynb)

description:

- web scraping system designed to fetch and process content from webpages. 
- It uses Playwright for browser automation, simulating human-like behavior such as scrolling and mouse movements to evade detection. 
- The Config class defines customizable parameters for user interaction simulation, timeouts, retries, and logging. 
- The asynchronous functions manage tasks like content extraction, retry mechanisms for failed requests, and processing a batch of URLs from a DataFrame. 
- Finally, the scraped data is saved to a JSON file with error handling to ensure reliability and robustness. This system is suitable for scalable and dynamic content extraction workflows.

