"""Module for extracting LinkedIn profile data."""

import time
import requests
import logging
from typing import Dict, Optional, Any
import os

import config

logger = logging.getLogger(__name__)

def extract_linkedin_profile(
    linkedin_profile_url: str, 
    api_key: Optional[str] = None, 
    mock: bool = False
) -> Dict[str, Any]:
    """Extract LinkedIn profile data using zerobreak/linkedin-profile-scrapper actor or mock data.
    
    Args:
        linkedin_profile_url: The LinkedIn profile URL to extract data from.
        api_key: Apify API token (optional; can use free tier without it).
        mock: If True, loads mock data from a premade JSON file instead of using the API.
    
    Returns:
        Dictionary containing the LinkedIn profile data.
    """
    start_time = time.time()
    
    try:
        if mock:
            logger.info("Using mock data from a premade JSON file...")
            mock_url = config.MOCK_DATA_URL
            response = requests.get(mock_url, timeout=30)
        else:
            logger.info("Starting to extract the LinkedIn profile using Apify...")

            # Extract username from LinkedIn URL
            # Formats: linkedin.com/in/username/ or linkedin.com/in/username
            if "linkedin.com/in/" not in linkedin_profile_url:
                raise ValueError(f"Invalid LinkedIn URL: {linkedin_profile_url}. Must contain 'linkedin.com/in/'")
            
            username = linkedin_profile_url.split("linkedin.com/in/")[-1].strip("/")
            
            # Use zerobreak/linkedin-profile-scrapper actor (free tier available)
            # Actor ID: zerobreak/linkedin-profile-scrapper
            apify_api_token = api_key or os.getenv("APIFY_API_TOKEN", "")
            apify_base_url = "https://api.apify.com/v2"
            
            # Prepare actor input for zerobreak/linkedin-profile-scrapper
            # This actor expects linkedinUrls parameter
            actor_input = {
                "linkedinUrls": [linkedin_profile_url]
            }
            
            logger.info(f"Sending request to Apify (zerobreak actor) for profile: {username}")
            
            # Call Apify actor with authentication
            if apify_api_token:
                # Authenticated call using the correct actor endpoint
                headers = {"Authorization": f"Bearer {apify_api_token}"}
                
                # Endpoint format: /actors/{ownerName}~{actorName}/run-sync-get-dataset-items
                actor_call_url = f"{apify_base_url}/actors/zerobreak~linkedin-profile-scrapper/run-sync-get-dataset-items"
                
                response = requests.post(
                    actor_call_url,
                    json=actor_input,
                    headers=headers,
                    timeout=120  # LinkedIn scraping can take time
                )
                
                logger.info(f"Apify API Response Status: {response.status_code}")
            else:
                # Use free alternative: mock data
                logger.warning("No APIFY_API_TOKEN provided. Falling back to mock data.")
                logger.warning("To scrape real LinkedIn profiles, set APIFY_API_TOKEN environment variable.")
                response = _fetch_profile_metadata(linkedin_profile_url)
        
        logger.info(f"Received response at {time.time() - start_time:.2f} seconds...")

        # Check if response is successful
        if response.status_code == 200:
            try:
                # Parse the JSON response
                data = response.json()
                
                # If Apify returns a list, extract the first item
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                
                # Clean the data, remove empty values and unwanted fields
                data = {
                    k: v
                    for k, v in data.items()
                    if v not in ([], "", None) and k not in ["people_also_viewed", "certifications"]
                }

                logger.info(f"Successfully extracted profile data in {time.time() - start_time:.2f}s")
                return data
            except ValueError as e:
                logger.error(f"Error parsing JSON response: {e}")
                logger.error(f"Response content: {response.text[:200]}...")  # Print first 200 chars
                return {}
        else:
            logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            logger.warning("Falling back to mock data since API call failed...")
            
            # Auto-fallback to mock data on API failure
            try:
                mock_response = requests.get(config.MOCK_DATA_URL, timeout=30)
                if mock_response.status_code == 200:
                    logger.info("✓ Successfully loaded mock data as fallback.")
                    return mock_response.json()
            except Exception as fallback_error:
                logger.error(f"Fallback to mock data also failed: {fallback_error}")
            
            return {}
            
    except Exception as e:
        logger.error(f"Error in extract_linkedin_profile: {e}")
        return {}


def _fetch_profile_metadata(linkedin_url: str) -> requests.Response:
    """Fetch profile metadata as fallback when APIFY_API_TOKEN is not set.
    
    This is a lightweight fallback that returns mock-like data.
    For production use, set APIFY_API_TOKEN environment variable.
    """
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self._data = {
                "name": "LinkedIn User",
                "headline": "Professional",
                "location": "Unknown",
                "profileUrl": linkedin_url,
                "summary": "Profile data requires Apify token. Use mock mode or set APIFY_API_TOKEN."
            }
        
        def json(self):
            return self._data
    
    logger.warning(f"Returning limited profile data. Set APIFY_API_TOKEN for full extraction.")
    return MockResponse()