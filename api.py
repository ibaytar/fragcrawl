"""
FastAPI application for fragrance scraping using crawl4ai.
This API allows users to send URLs of fragrance pages and receive structured JSON data.
"""

import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import asyncio
from urllib.parse import urlparse, unquote

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Define the CSS schema for extraction
css_schema = {
    "baseSelector": "body",
    "fields": [
        {
            "name": "title",
            "selector": "#toptop > h1",
            "type": "text"
        },
        {
            "name": "sex",
            "selector": "#toptop > h1 > small",
            "type": "text"
        },
        {
            "name": "image",
            "selector": ".text-center .small-12 img",
            "type": "attribute",
            "attribute": "src"
        },
        {
            "name": "accords",
            "selector": ".accord-bar",
            "type": "list",
            "fields": [
                {"name": "text", "type": "text"}
            ]
        },
        {
            "name": "has_top_notes",
            "selector": "#pyramid h4:contains('Top Notes')",
            "type": "exists"
        },
        {
            "name": "has_middle_notes",
            "selector": "#pyramid h4:contains('Middle Notes')",
            "type": "exists"
        },
        {
            "name": "has_base_notes",
            "selector": "#pyramid h4:contains('Base Notes')",
            "type": "exists"
        },
        {
            "name": "top_notes",
            "selector": "#pyramid h4:contains('Top Notes') + div div[style*='justify-content: center'] > div:has(div:nth-child(2))",
            "type": "nested_list",
            "fields": [
                {
                    "name": "name",
                    "selector": "div:nth-child(2)",
                    "type": "text"
                },
                {
                    "name": "image",
                    "selector": "img",
                    "type": "attribute",
                    "attribute": "src"
                }
            ]
        },
        {
            "name": "middle_notes",
            "selector": "#pyramid h4:contains('Middle Notes') + div div[style*='justify-content: center'] > div:has(div:nth-child(2))",
            "type": "nested_list",
            "fields": [
                {
                    "name": "name",
                    "selector": "div:nth-child(2)",
                    "type": "text"
                },
                {
                    "name": "image",
                    "selector": "img",
                    "type": "attribute",
                    "attribute": "src"
                }
            ]
        },
        {
            "name": "base_notes",
            "selector": "#pyramid h4:contains('Base Notes') + div div[style*='justify-content: center'] > div:has(div:nth-child(2))",
            "type": "nested_list",
            "fields": [
                {
                    "name": "name",
                    "selector": "div:nth-child(2)",
                    "type": "text"
                },
                {
                    "name": "image",
                    "selector": "img",
                    "type": "attribute",
                    "attribute": "src"
                }
            ]
        },
        {
            "name": "unclassified_notes",
            "selector": "#pyramid .notes-box + div div[style*='justify-content: center'] > div:has(div:nth-child(2))",
            "type": "nested_list",
            "fields": [
                {
                    "name": "name",
                    "selector": "div:nth-child(2)",
                    "type": "text"
                },
                {
                    "name": "image",
                    "selector": "img",
                    "type": "attribute",
                    "attribute": "src"
                }
            ]
        }
    ],
}

# Create the extraction strategy
css_strategy = JsonCssExtractionStrategy(schema=css_schema)

# Create the FastAPI app
app = FastAPI(
    title="Fragrance Scraper API",
    description="API for scraping fragrance data from Fragrantica",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Define the request model
class ScrapeRequest(BaseModel):
    urls: List[HttpUrl]

# Define the response model
class FragranceData(BaseModel):
    title: Optional[str] = None
    sex: Optional[str] = None
    image: Optional[str] = None
    accords: Optional[List[str]] = None
    notes: Optional[Dict[str, List[Dict[str, str]]]] = None
    house: Optional[str] = None
    perfume_name: Optional[str] = None

class ScrapeResponse(BaseModel):
    results: List[FragranceData]
    errors: List[Dict[str, str]] = []

async def process_url(url: str, crawler: AsyncWebCrawler) -> Dict[str, Any]:
    """Process a single URL and return the extracted data"""
    try:
        # Configure the crawler run settings
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=css_strategy,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter()
            )
        )

        # Run the crawler
        result = await crawler.arun(url=url, config=config)

        if not result.success:
            error_msg = f"Failed to crawl {url}: {result.error_message}"
            print(f"Error: {error_msg}")
            return {"error": error_msg}

        try:
            # Parse the extracted content
            data = json.loads(result.extracted_content)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON from {url}: {str(e)}"
            print(f"Error: {error_msg}")
            return {"error": error_msg}

        if not data or len(data) == 0:
            return {"error": f"No data extracted from {url}"}

        # Process the extracted data
        item = data[0]

        # Transform the accords from list of objects to list of strings
        if "accords" in item:
            item["accords"] = [accord["text"] for accord in item["accords"]]

        # Process notes data
        notes = {}

        # Check if we have classified notes
        has_classified_notes = False
        if "has_top_notes" in item and item["has_top_notes"]:
            has_classified_notes = True
        if "has_middle_notes" in item and item["has_middle_notes"]:
            has_classified_notes = True
        if "has_base_notes" in item and item["has_base_notes"]:
            has_classified_notes = True

        # Process top notes
        if "top_notes" in item:
            if item["top_notes"]:
                notes["top"] = item["top_notes"]
            del item["top_notes"]

        # Process middle notes
        if "middle_notes" in item:
            if item["middle_notes"]:
                notes["middle"] = item["middle_notes"]
            del item["middle_notes"]

        # Process base notes
        if "base_notes" in item:
            if item["base_notes"]:
                notes["base"] = item["base_notes"]
            del item["base_notes"]

        # Process unclassified notes if we don't have classified notes
        if "unclassified_notes" in item:
            if not has_classified_notes and item["unclassified_notes"]:
                notes["unclassified"] = item["unclassified_notes"]
            del item["unclassified_notes"]

        # Clean up the data
        if "has_top_notes" in item:
            del item["has_top_notes"]
        if "has_middle_notes" in item:
            del item["has_middle_notes"]
        if "has_base_notes" in item:
            del item["has_base_notes"]

        # Add the processed notes to the data
        item["notes"] = notes

        # Extract house and perfume name from URL
        parsed_url = urlparse(url)
        path_parts = unquote(parsed_url.path).split('/')
        if len(path_parts) >= 4 and path_parts[1] == "perfume":
            # Get house name and replace hyphens with spaces
            house = path_parts[2].replace('-', ' ')

            # Get perfume name and remove any ID numbers at the end (like -590)
            perfume_name_raw = path_parts[3].split('.html')[0]
            # Remove any trailing numbers (like -590) and replace hyphens with spaces
            perfume_name = ' '.join(perfume_name_raw.split('-')[:-1] if perfume_name_raw.split('-')[-1].isdigit() else perfume_name_raw.split('-'))

            # Add house and perfume name to the data
            item["house"] = house
            item["perfume_name"] = perfume_name

            # Clean up the title by removing the "for women and men" or "for men" part
            if "sex" in item and item["sex"] and "title" in item:
                item["title"] = item["title"].replace(item["sex"], "")

        return item
    except Exception as e:
        return {"error": f"Error processing {url}: {str(e)}"}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_fragrances(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape fragrance data from the provided URLs
    """
    # Configure browser settings for Docker environment
    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )

    # Note: If you need to pass browser arguments, check the version of crawl4ai
    # For newer versions, you might use:
    # browser_config = BrowserConfig(
    #     headless=True,
    #     verbose=False,
    #     browser_args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
    # )

    results = []
    errors = []

    # Use context manager for proper resource handling
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Process each URL
        tasks = [process_url(str(url), crawler) for url in request.urls]
        processed_results = await asyncio.gather(*tasks)

        for result in processed_results:
            if "error" in result:
                errors.append(result)
            else:
                results.append(result)

    return ScrapeResponse(results=results, errors=errors)

@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "name": "Fragrance Scraper API",
        "version": "1.0.0",
        "description": "API for scraping fragrance data from Fragrantica",
        "endpoints": {
            "/scrape": "POST - Scrape fragrance data from provided URLs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
