import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

from ml.local_inference import local_inference

class AzureMLService:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_ML_ENDPOINT")
        self.api_key = os.getenv("AZURE_ML_API_KEY")

    def predict(self, input_data):
        """
        [LOCAL MODE] Uses the local .pkl model for predictions.
        """
        try:
            # Extract data from the standard Azure ML format we were using
            # {"data": [{"product": name, "stock": s, "price_per_unit": p, ...}]}
            data = input_data.get("data", [])
            if not data:
                return None
                
            item = data[0]
            product_name = item.get("product")
            stock = item.get("stock")
            price = item.get("price_per_unit")
            
            prediction = local_inference.predict(product_name, stock, price)
            
            # Return in a format similar to what we expect
            return [prediction] if prediction is not None else None
        except Exception as e:
            print(f"Local ML redirection error: {e}")
            return None

# Singleton instance
azure_ml_service = AzureMLService()
