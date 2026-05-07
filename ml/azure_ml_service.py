import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class AzureMLService:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_ML_ENDPOINT")
        self.api_key = os.getenv("AZURE_ML_API_KEY")

    def predict(self, input_data):
        """
        Calls the Azure ML Online Endpoint.
        input_data: list of dicts/lists as required by the model.
        """
        if not self.endpoint or not self.api_key:
            print("Azure ML Endpoint or API Key not found in .env")
            return None

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        # Use the input_data directly as the payload
        payload = input_data

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers)
            print(f"Azure ML Response Status: {response.status_code}")
            print(f"Azure ML Response Body: {response.text}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling Azure ML: {e}")
            return None

# Singleton instance
azure_ml_service = AzureMLService()
