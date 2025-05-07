"""
Example demonstrating different extraction strategies with various input formats.
This example shows how to:
1. Use different input formats (markdown, HTML, fit_markdown)
2. Work with JSON-based extractors (CSS and XPath)
3. Use LLM-based extraction with different input formats
4. Configure browser and crawler settings properly
"""

import asyncio
import os
import json
from urllib.parse import urlparse, unquote

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import LLMConfig
from crawl4ai.extraction_strategy import (JsonCssExtractionStrategy)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def run_extraction(crawler: AsyncWebCrawler, url: str, strategy, name: str):
    """Helper function to run extraction with proper configuration"""
    try:
        # Configure the crawler run settings
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=strategy,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter()  # For fit_markdown support
            )
        )

        # Run the crawler
        result = await crawler.arun(url=url, config=config)

        if result.success:
            import json
            from urllib.parse import urlparse, unquote

            # Parse the extracted content
            data = json.loads(result.extracted_content)

            if data and len(data) > 0:
                # Transform the accords from list of objects to list of strings
                if "accords" in data[0]:
                    data[0]["accords"] = [item["text"] for item in data[0]["accords"]]

                # Process notes data
                notes = {}

                # Check if we have classified notes
                has_classified_notes = False
                if "has_top_notes" in data[0] and data[0]["has_top_notes"]:
                    has_classified_notes = True
                if "has_middle_notes" in data[0] and data[0]["has_middle_notes"]:
                    has_classified_notes = True
                if "has_base_notes" in data[0] and data[0]["has_base_notes"]:
                    has_classified_notes = True

                # Process top notes
                if "top_notes" in data[0]:
                    if data[0]["top_notes"]:
                        notes["top"] = data[0]["top_notes"]
                    del data[0]["top_notes"]

                # Process middle notes
                if "middle_notes" in data[0]:
                    if data[0]["middle_notes"]:
                        notes["middle"] = data[0]["middle_notes"]
                    del data[0]["middle_notes"]

                # Process base notes
                if "base_notes" in data[0]:
                    if data[0]["base_notes"]:
                        notes["base"] = data[0]["base_notes"]
                    del data[0]["base_notes"]

                # Process unclassified notes if we don't have classified notes
                if "unclassified_notes" in data[0]:
                    if not has_classified_notes and data[0]["unclassified_notes"]:
                        notes["unclassified"] = data[0]["unclassified_notes"]
                    del data[0]["unclassified_notes"]

                # Clean up the data
                if "has_top_notes" in data[0]:
                    del data[0]["has_top_notes"]
                if "has_middle_notes" in data[0]:
                    del data[0]["has_middle_notes"]
                if "has_base_notes" in data[0]:
                    del data[0]["has_base_notes"]

                # Add the processed notes to the data
                data[0]["notes"] = notes

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
                    data[0]["house"] = house
                    data[0]["perfume_name"] = perfume_name

                    # Clean up the title by removing the "for women and men" or "for men" part
                    if "sex" in data[0] and data[0]["sex"] and "title" in data[0]:
                        data[0]["title"] = data[0]["title"].replace(data[0]["sex"], "")

            print(f"\n=== {name} Results ===")
            print(f"Extracted Content: {json.dumps(data, indent=4)}")
            print(f"Raw Markdown Length: {len(result.markdown.raw_markdown)}")
            print(
                f"Citations Markdown Length: {len(result.markdown.markdown_with_citations)}"
            )
        else:
            print(f"Error in {name}: Crawl failed")

    except Exception as e:
        print(f"Error in {name}: {str(e)}")


async def extract_fragrance_data(url, output_file=None):
    """Extract fragrance data from a URL and optionally save to a file"""
    # Configure browser settings
    browser_config = BrowserConfig(headless=True, verbose=True)

    # Initialize CSS extraction strategy
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
    css_strategy = JsonCssExtractionStrategy(schema=css_schema)

    # Use context manager for proper resource handling
    result_data = None
    async with AsyncWebCrawler(config=browser_config) as crawler:
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

        if result.success:
            # Parse the extracted content
            data = json.loads(result.extracted_content)

            if data and len(data) > 0:
                # Process the data
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

                # Save the result
                result_data = item

                # Print the result
                print(f"\n=== Extraction Results ===")
                print(f"Extracted Content: {json.dumps(item, indent=4)}")

                # Save to file if specified
                if output_file:
                    with open(output_file, 'w') as f:
                        json.dump(item, f, indent=4)
            else:
                print(f"Error: No data extracted")
        else:
            print(f"Error: Crawl failed - {result.error_message}")

    return result_data

async def main():
    """Main function that parses command line arguments and runs the extraction"""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract fragrance data from Fragrantica')
    parser.add_argument('--url', type=str, required=True, help='URL of the fragrance page')
    parser.add_argument('--output', type=str, help='Output file path (JSON)')

    args = parser.parse_args()

    # Run the extraction
    await extract_fragrance_data(args.url, args.output)

if __name__ == "__main__":
    asyncio.run(main())