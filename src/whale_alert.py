import requests
import os
from dotenv import load_dotenv

load_dotenv()

class WhaleTracker:
    def __init__(self):
        self.api_key = os.getenv("WHALE_ALERT_API_KEY")
        self.base_url = "https://api.whale-alert.io/v1"

        if not self.api_key:
            print("WARNING: WHALE_ALERT_API_KEY not found in .env. Whale tracking will be disabled.")

    def get_recent_transactions(self, min_value=1000000):
        """
        Fetch recent large transactions (whales).
        min_value defaults to 1,000,000 USD.
        """
        if not self.api_key:
            return []

        endpoint = f"{self.base_url}/transactions"
        params = {
            "api_key": self.api_key,
            "min_value": min_value
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("transactions", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Whale Alert data: {e}")
            return []
