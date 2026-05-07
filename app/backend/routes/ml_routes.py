from flask import Blueprint, jsonify, request
from agents.forecast_agent import forecast_agent
from ..extensions import get_db_connection
from utils.helpers import admin_required

ml_bp = Blueprint("ml", __name__)

@ml_bp.route("/predictions", methods=["GET"])
@admin_required
def get_predictions():
    """
    Predict demand for all active products for the current day using Forecast Agent.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all products
    cursor.execute("SELECT name, stock, unit FROM product")
    products = cursor.fetchall()
    conn.close()
    
    results = []
    for p in products:
        # Use Forecast Agent to get predictions from Azure ML
        prediction_data = forecast_agent.predict_product_demand(p.name)
        
        if "error" in prediction_data:
            pred_val = 0
        else:
            pred_val = prediction_data["predicted_demand"]
        
        results.append({
            "product_name": p.name,
            "current_stock": p.stock,
            "unit": p.unit,
            "predicted_demand": pred_val,
            "status": "High Demand" if pred_val > p.stock else "Normal"
        })
    
    # Sort by demand to show most important ones first
    results.sort(key=lambda x: x['predicted_demand'], reverse=True)
    
    return jsonify({"predictions": results}), 200

@ml_bp.route("/predict/<string:product_name>", methods=["GET"])
@admin_required
def predict_single(product_name):
    """
    Get detailed prediction for a single product.
    """
    result = forecast_agent.predict_product_demand(product_name)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 200
