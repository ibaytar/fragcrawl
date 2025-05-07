"""
Standalone crawler microservice that can be used by multiple projects
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any
import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

app = FastAPI(title="Crawler Microservice")

class CrawlRequest(BaseModel):
    url: HttpUrl
    css_schema: Dict[str, Any]

@app.post("/crawl")
async def crawl(request: CrawlRequest):
    browser_config = BrowserConfig(headless=True)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        strategy = JsonCssExtractionStrategy(schema=request.css_schema)
        config = CrawlerRunConfig(
            cache_mode=CacheMode.USE_CACHE,  # Use cache to save resources
            extraction_strategy=strategy
        )
        
        result = await crawler.arun(url=str(request.url), config=config)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)
            
        return {"data": result.extracted_content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("crawler_service:app", host="0.0.0.0", port=8001)