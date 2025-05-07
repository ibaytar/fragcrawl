"""
Test script for the Fragrance Scraper API.
This script sends a request to the API and prints the response.
"""

import requests
import json
import sys

def test_api(urls):
    """Test the API by sending a request with the provided URLs"""
    try:
        # API endpoint
        api_url = "http://localhost:8000/scrape"

        # Request payload
        payload = {
            "urls": urls
        }

        print(f"Sending request to {api_url} with {len(urls)} URLs...")

        # Send the request
        response = requests.post(api_url, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            data = response.json()

            # Print the raw JSON response
            print("\nRaw JSON Response:")
            print(json.dumps(data, indent=2))

            # Print the results
            print("\nAPI Response:")
            print(f"Results: {len(data['results'])}")
            print(f"Errors: {len(data['errors'])}")

            # Print the results in a formatted way
            print("\nExtracted Fragrances:")
            for i, result in enumerate(data['results']):
                print(f"\n--- Fragrance {i+1} ---")
                print(f"Title: {result.get('title', 'N/A')}")
                print(f"House: {result.get('house', 'N/A')}")
                print(f"Perfume Name: {result.get('perfume_name', 'N/A')}")
                print(f"Sex: {result.get('sex', 'N/A')}")
                print(f"Image: {result.get('image', 'N/A')}")

                # Print accords
                if 'accords' in result and result['accords']:
                    print(f"Accords: {', '.join(result['accords'])}")
                else:
                    print("Accords: None")

                # Print notes
                if 'notes' in result and result['notes']:
                    print("\nNotes:")
                    for category, notes in result['notes'].items():
                        print(f"  {category.capitalize()} Notes:")
                        for note in notes:
                            note_name = note.get('name', 'N/A')
                            note_image = note.get('image', 'N/A')
                            print(f"    - {note_name} (Image: {note_image})")
                else:
                    print("\nNotes: None")

            # Print any errors
            if data['errors']:
                print("\nErrors:")
                for error in data['errors']:
                    print(f"- {error}")
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the API server is running.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Default URLs to test
    default_urls = [
        "https://www.fragrantica.com/perfume/Davidoff/Zino-Davidoff-590.html",
        "https://www.fragrantica.com/perfume/Louis-Vuitton/Afternoon-Swim-53947.html"
    ]

    # Use command line arguments if provided, otherwise use default URLs
    if len(sys.argv) > 1:
        urls = sys.argv[1:]
    else:
        urls = default_urls

    # Test the API
    test_api(urls)
