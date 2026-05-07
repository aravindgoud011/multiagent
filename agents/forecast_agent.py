import datetime
from ml.azure_ml_service import azure_ml_service
from app.backend.extensions import get_db_connection

class ForecastAgent:
    """
    Forecast Agent: Responsible for generating demand predictions using Azure ML.
    """
    
    def get_product_mapping(self):
        """Reconstructs alphabetical LabelEncoder mapping from DB."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM product")
            products = [row[0] for row in cursor.fetchall()]
            products.sort()
            conn.close()
            return {name: i for i, name in enumerate(products)}
        except:
            return {}

    def predict_product_demand(self, product_name):
        """
        Predicts demand for a specific product using encoded features.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, stock, price FROM product WHERE name = ?", product_name)
        product = cursor.fetchone()
        conn.close()
        
        if not product:
            return {"error": f"Product '{product_name}' not found."}
            
        # 2. Prepare features for ML
        # Based on logs, score.py ALREADY has an encoder and expects the RAW STRING NAME
        is_weekend = 1 if datetime.datetime.now().weekday() >= 5 else 0
        
        # Standard Azure ML format: {"data": [{"key": val, ...}]}
        input_data = {
            "data": [
                {
                    "product": product.name,
                    "stock": float(product.stock),
                    "price_per_unit": float(product.price),
                    "weekend": int(is_weekend)
                }
            ]
        }
        
        # 3. Call Azure ML
        prediction_response = azure_ml_service.predict(input_data)
        
        if prediction_response is not None:
            # Check for different possible response formats from Azure ML
            res = None
            if isinstance(prediction_response, (int, float)):
                res = prediction_response
            elif isinstance(prediction_response, list) and len(prediction_response) > 0:
                res = prediction_response[0]
            elif isinstance(prediction_response, dict):
                # Try common keys
                res_list = prediction_response.get("result", 
                           prediction_response.get("Results", 
                           prediction_response.get("data", None)))
                
                if isinstance(res_list, list) and len(res_list) > 0:
                    res = res_list[0]
                elif isinstance(res_list, (int, float)):
                    res = res_list
            
            if res is not None:
                return {
                    "product_name": product_name,
                    "current_stock": product.stock,
                    "predicted_demand": round(float(res), 2),
                    "is_weekend": bool(is_weekend)
                }
            
        return {"error": "Prediction service unavailable."}

# Singleton instance
forecast_agent = ForecastAgent()
