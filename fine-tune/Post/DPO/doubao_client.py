"""
Doubao API client for text augmentation
"""

import requests
import time
import json
from typing import Optional, Dict, Any
from config import (
    DOUBAO_API_KEY,
    DOUBAO_API_ENDPOINT,
    DOUBAO_MODEL,
    MAX_RETRIES,
    RETRY_DELAY,
    REQUEST_TIMEOUT,
)


class DoubaoClient:
    """Client for interacting with Doubao API"""
    
    def __init__(self):
        self.api_key = DOUBAO_API_KEY
        self.endpoint = DOUBAO_API_ENDPOINT
        self.model = DOUBAO_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def augment_option(
        self, 
        option_text: str,
        context: str,
        chosen_text: str,
        rejected_text: str,
        chosen_votes: int,
        rejected_votes: int,
        chosen_percentage: str,
        rejected_percentage: str,
        is_chosen: bool = True
    ) -> Optional[str]:
        """
        Generate analysis for why an option is chosen or rejected
        
        Args:
            option_text: The option being analyzed
            context: Job seeker's background and question
            chosen_text: The winning option text
            rejected_text: The losing option text
            chosen_votes: Votes for chosen option
            rejected_votes: Votes for rejected option
            chosen_percentage: Percentage for chosen option
            rejected_percentage: Percentage for rejected option
            is_chosen: True if analyzing chosen option, False for rejected
            
        Returns:
            Analysis text or None if failed
        """
        from config import CHOSEN_PROMPT, REJECTED_PROMPT
        
        # Select appropriate prompt
        if is_chosen:
            prompt = CHOSEN_PROMPT.format(
                chosen_text=chosen_text,
                rejected_text=rejected_text,
                context=context,
                chosen_votes=chosen_votes,
                rejected_votes=rejected_votes,
                chosen_percentage=chosen_percentage,
                rejected_percentage=rejected_percentage
            )
        else:
            prompt = REJECTED_PROMPT.format(
                chosen_text=chosen_text,
                rejected_text=rejected_text,
                context=context,
                chosen_votes=chosen_votes,
                rejected_votes=rejected_votes,
                chosen_percentage=chosen_percentage,
                rejected_percentage=rejected_percentage
            )
        
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Parse Doubao API response structure
                    if "output" in result and len(result["output"]) > 0:
                        # Iterate through output items to find the message with output_text
                        for output_item in result["output"]:
                            if output_item.get("type") == "message":
                                content = output_item.get("content", [])
                                for content_item in content:
                                    if content_item.get("type") == "output_text":
                                        text = content_item.get("text", "").strip()
                                        if text:
                                            return text
                    
                    # Fallback: try standard OpenAI-style response
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0].get("message", {}).get("content", "").strip()
                    
                    print(f"Warning: Could not extract text from response")
                    return None
                    
                elif response.status_code == 429:  # Rate limit
                    print(f"Rate limited, retrying in {RETRY_DELAY * (attempt + 1)} seconds...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                    
                else:
                    print(f"API error: {response.status_code} - {response.text}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return None
                
            except Exception as e:
                print(f"Error calling Doubao API: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return None
        
        return None


if __name__ == "__main__":
    # Test the client
    client = DoubaoClient()
    
    # Test data
    context = "本人双9硕，计算机专业，想找一个稳定的工作"
    chosen_text = "华为ICT数通"
    rejected_text = "小公司开发岗"
    
    print(f"Testing chosen option analysis...")
    result = client.augment_option(
        option_text=chosen_text,
        context=context,
        chosen_text=chosen_text,
        rejected_text=rejected_text,
        chosen_votes=26,
        rejected_votes=11,
        chosen_percentage="70.3%",
        rejected_percentage="29.7%",
        is_chosen=True
    )
    print(f"Chosen analysis: {result}")
