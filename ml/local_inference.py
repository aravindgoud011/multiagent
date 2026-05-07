import pickle
import pandas as pd
import os
import datetime

class LocalMLInference:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
        self.model_data = None
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.model_data = pickle.load(f)
            print("Local ML Model loaded successfully.")
        else:
            print(f"Local ML Model not found at {self.model_path}")

    def predict(self, product_name, stock, price):
        if not self.model_data:
            return None
            
        model = self.model_data["model"]
        le = self.model_data["label_encoder"]
        
        # Prepare features
        try:
            # Handle unseen products by using a default or closest match
            if product_name in le.classes_:
                product_encoded = le.transform([product_name])[0]
            else:
                # Use a default encoding (e.g., index 0)
                product_encoded = 0
                
            now = datetime.datetime.now()
            day_of_week = now.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # features = ['product_encoded', 'stock', 'price', 'day_of_week', 'is_weekend']
            input_df = pd.DataFrame([{
                "product_encoded": product_encoded,
                "stock": stock,
                "price": price,
                "day_of_week": day_of_week,
                "is_weekend": is_weekend
            }])
            
            prediction = model.predict(input_df)[0]
            return max(1, int(round(float(prediction))))
        except Exception as e:
            print(f"Inference error: {e}")
            return None

# Singleton
local_inference = LocalMLInference()
