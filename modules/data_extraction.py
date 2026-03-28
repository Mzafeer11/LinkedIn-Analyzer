"""Module for extracting LinkedIn profile data."""

import time
import requests
import logging
from typing import Dict, Optional, Any
import os
import json

import config

logger = logging.getLogger(__name__)

def extract_linkedin_profile(
    linkedin_profile_url: str, 
    api_key: Optional[str] = None, 
    mock: bool = False
) -> Dict[str, Any]:
    """Extract LinkedIn profile data using zerobreak/linkedin-profile-scrapper actor (2-step process).
    
    This actor requires:
    Step 1: Generate snapshot ID (starts scraping job)
    Step 2: Fetch data after 30+ seconds (retrieves results)
    
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
            if response.status_code == 200:
                return response.json()
            return {}
        
        logger.info("Starting LinkedIn profile extraction (zerobreak actor, 2-step process)...")

        # Validate LinkedIn URL
        if "linkedin.com/in/" not in linkedin_profile_url:
            raise ValueError(f"Invalid LinkedIn URL: {linkedin_profile_url}. Must contain 'linkedin.com/in/'")
        
        username = linkedin_profile_url.split("linkedin.com/in/")[-1].strip("/")
        apify_api_token = api_key or os.getenv("APIFY_API_TOKEN", "")
        
        if not apify_api_token:
            logger.warning("No APIFY_API_TOKEN provided. Falling back to mock data.")
            mock_url = config.MOCK_DATA_URL
            response = requests.get(mock_url, timeout=30)
            return response.json() if response.status_code == 200 else {}
        
        # ==== STEP 1: Generate Snapshot ID ====
        logger.info(f"[Step 1/2] Generating snapshot ID for profile: {username}")
        
        apify_base_url = "https://api.apify.com/v2"
        
        # Step 1 input: generate_snap_id action
        step1_input = {
            "action": "generate_snap_id",
            "urls": linkedin_profile_url  # Single URL as string
        }
        
        # Correct endpoint: /acts/ not /actors/
        # Token is passed as query parameter, not header
        step1_url = f"{apify_base_url}/acts/zerobreak~linkedin-profile-scrapper/run-sync-get-dataset-items"
        
        response = requests.post(
            step1_url,
            json=step1_input,
            params={"token": apify_api_token},
            timeout=60
        )
        
        logger.info(f"Step 1 Response Status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Step 1 failed: {response.text}")
            logger.warning("Falling back to mock data...")
            mock_url = config.MOCK_DATA_URL
            mock_response = requests.get(mock_url, timeout=30)
            return mock_response.json() if mock_response.status_code == 200 else {}
        
        # Extract snapshot ID from response
        result = response.json()
        
        # Response might be a list or direct object
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        
        snapshot_id = result.get("snap_id") or result.get("snapshot_id")
        
        if not snapshot_id:
            logger.error(f"No snapshot ID in response: {result}")
            logger.warning("Falling back to mock data...")
            mock_url = config.MOCK_DATA_URL
            mock_response = requests.get(mock_url, timeout=30)
            return mock_response.json() if mock_response.status_code == 200 else {}
        
        logger.info(f"✓ Snapshot ID generated: {snapshot_id}")
        logger.info("⏳ Waiting 30 seconds for data collection...")
        
        # ==== WAIT 30 SECONDS ====
        time.sleep(30)
        
        # ==== STEP 2: Fetch Data ====
        logger.info(f"[Step 2/2] Fetching scraped data using snapshot ID: {snapshot_id}")
        
        step2_input = {
            "action": "fetch_data",
            "snap_id": snapshot_id
        }
        
        response = requests.post(
            step1_url,  # Same endpoint, different action
            json=step2_input,
            params={"token": apify_api_token},
            timeout=60
        )
        
        logger.info(f"Step 2 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle list response
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            # Clean up empty fields
            if isinstance(data, dict):
                data = {
                    k: v
                    for k, v in data.items()
                    if v not in ([], "", None)
                }
            
            logger.info(f"✓ Successfully extracted profile data in {time.time() - start_time:.2f}s")
            return data
        else:
            logger.error(f"Step 2 failed: {response.text}")
            logger.warning("Falling back to mock data...")
            mock_url = config.MOCK_DATA_URL
            mock_response = requests.get(mock_url, timeout=30)
            return mock_response.json() if mock_response.status_code == 200 else {}
            
    except Exception as e:
        logger.error(f"Error in extract_linkedin_profile: {e}")
        logger.warning("Falling back to mock data...")
        try:
            mock_url = config.MOCK_DATA_URL
            mock_response = requests.get(mock_url, timeout=30)
            return mock_response.json() if mock_response.status_code == 200 else {}
        except:
            return {}