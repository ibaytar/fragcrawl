"""
Simple FastAPI application for fragrance scraping using subprocess to run the scraper.
This API allows users to send URLs of fragrance pages and receive structured JSON data.
"""

import json
import subprocess
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

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

def run_scraper(url: str) -> Dict[str, Any]:
    """Run the scraper for a single URL using subprocess"""
    try:
        # Create a temporary file to store the output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_file:
            temp_file_path = temp_file.name
        
        # Run the scraper and save the output to the temporary file
        cmd = [
            "python", 
            "app.py", 
            "--url", 
            url,
            "--output",
            temp_file_path
        ]
        
        # Run the command
        process = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Read the output from the temporary file
        with open(temp_file_path, 'r') as f:
            result = json.load(f)
        
        return result
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to scrape {url}: {e.stderr}"}
    except Exception as e:
        return {"error": f"Error processing {url}: {str(e)}"}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_fragrances(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape fragrance data from the provided URLs
    """
    results = []
    errors = []
    
    # Process each URL
    for url in request.urls:
        result = run_scraper(str(url))
        
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
    uvicorn.run("simple_api:app", host="0.0.0.0", port=8000, reload=True)
