# Fragrance Scraper API

A FastAPI application for scraping fragrance data from Fragrantica.

## Features

- Extract fragrance details including:
  - Title and brand
  - Gender classification
  - Image URL
  - Accords
  - Notes (top, middle, base, or unclassified)
  - House and perfume name

## Installation

### Option 1: Local Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
playwright install
```

### Option 2: Docker Installation (Recommended)

1. Clone this repository
2. Build and start the Docker container using the provided script:

```bash
./run.sh
```

Or manually with Docker Compose:

```bash
docker-compose up --build
```

## Usage

### Starting the API server

#### Local Installation

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

#### Docker Installation

Using the provided script:

```bash
# Build and start the container
./run.sh

# Start the container
./run.sh start

# Stop the container
./run.sh stop

# View logs
./run.sh logs

# Run tests
./run.sh test
```

Or manually with Docker Compose:

```bash
# Build and start the container
docker-compose up --build

# Start the container in detached mode
docker-compose up -d

# Stop the container
docker-compose down

# View logs
docker-compose logs -f
```

The API will be available at http://localhost:8000

### API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoints

#### POST /scrape

Scrape fragrance data from the provided URLs.

**Request Body:**

```json
{
  "urls": [
    "https://www.fragrantica.com/perfume/Davidoff/Zino-Davidoff-590.html",
    "https://www.fragrantica.com/perfume/Louis-Vuitton/Afternoon-Swim-53947.html"
  ]
}
```

**Response:**

```json
{
  "results": [
    {
      "title": "Zino Davidoff Davidoff",
      "sex": "for men",
      "image": "https://fimgs.net/mdimg/perfume/375x500.590.jpg",
      "accords": ["woody", "aromatic", "patchouli", "warm spicy", "balsamic"],
      "notes": {
        "top": [
          {
            "name": "Brazilian Rosewood",
            "image": "https://fimgs.net/mdimg/sastojci/t.110.jpg"
          },
          {
            "name": "Lavender",
            "image": "https://fimgs.net/mdimg/sastojci/t.1.jpg"
          }
        ],
        "middle": [...],
        "base": [...]
      },
      "house": "Davidoff",
      "perfume_name": "Zino Davidoff"
    },
    {
      "title": "Afternoon Swim Louis Vuitton",
      "sex": "for women and men",
      "image": "https://fimgs.net/mdimg/perfume/375x500.53947.jpg",
      "accords": ["citrus", "fresh spicy"],
      "notes": {
        "unclassified": [
          {
            "name": "Mandarin Orange",
            "image": "https://fimgs.net/mdimg/sastojci/t.82.jpg"
          },
          {
            "name": "Sicilian Orange",
            "image": "https://fimgs.net/mdimg/sastojci/t.80.jpg"
          }
        ]
      },
      "house": "Louis Vuitton",
      "perfume_name": "Afternoon Swim"
    }
  ],
  "errors": []
}
```

## Example Usage with Python

```python
import requests

url = "http://localhost:8000/scrape"
payload = {
    "urls": [
        "https://www.fragrantica.com/perfume/Davidoff/Zino-Davidoff-590.html",
        "https://www.fragrantica.com/perfume/Louis-Vuitton/Afternoon-Swim-53947.html"
    ]
}

response = requests.post(url, json=payload)
data = response.json()
print(data)
```

## Example Usage with JavaScript/Fetch

```javascript
const url = "http://localhost:8000/scrape";
const payload = {
  urls: [
    "https://www.fragrantica.com/perfume/Davidoff/Zino-Davidoff-590.html",
    "https://www.fragrantica.com/perfume/Louis-Vuitton/Afternoon-Swim-53947.html",
  ],
};

fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify(payload),
})
  .then((response) => response.json())
  .then((data) => console.log(data))
  .catch((error) => console.error("Error:", error));
```

## Testing the API

You can test the API using the provided test script:

```bash
python docker_test.py
```

This will send a request to the API with two default URLs and print the response.

You can also specify your own URLs:

```bash
python docker_test.py "https://www.fragrantica.com/perfume/Davidoff/Zino-Davidoff-590.html" "https://www.fragrantica.com/perfume/Louis-Vuitton/Afternoon-Swim-53947.html"
```

## Troubleshooting

### Docker Issues

If you encounter issues with the Docker container, you can check the logs:

```bash
./run.sh logs
```

or

```bash
docker-compose logs
```

To rebuild the container from scratch:

```bash
./run.sh stop
./run.sh build
./run.sh start
```

or

```bash
docker-compose down
docker-compose up --build
```

If you're having issues with shared memory (browser crashes), you can increase the shared memory size in the docker-compose.yml file:

```yaml
services:
  fragrance-api:
    # ... other settings
    shm_size: "4gb" # Increase this value
```

### Playwright Issues

If you encounter issues with Playwright, make sure you have installed the browsers:

```bash
playwright install
```

For Docker, the browsers are installed automatically during the build process.

## License

MIT
