import pandas as pd
import numpy as np
import datetime
import random

# List of sample products with popularity scores (1-10)
# Scaled for a realistic Kirana/Small Retail shop daily volume
products = {
    "Rice 26kg": 2,      # 1-5 bags
    "Sugar": 8,          # 5-25 kg
    "Milk 1L": 10,       # 20-50 packets
    "Bread": 7,          # 10-20 loaves
    "Eggs 12pk": 8,      # 10-20 packs
    "Cooking Oil 5L": 2, # 1-4 cans
    "Dal 1kg": 6,        # 5-15 kg
    "Salt 1kg": 4,       # 3-10 kg
    "Tea 500g": 5,       # 2-8 packs
    "Coffee 200g": 4,    # 2-6 packs
    "greenchilli-100g": 9, # 20-40 packs
    "Redchilli-50g": 4,
    "GaramMasala": 3,
    "Curd-200g": 7,
    "garlic100g": 6,
    "ginger100g": 6
}

def generate_6_months_data():
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=180)
    
    data = []
    
    current_date = start_date
    while current_date <= end_date:
        is_weekend = 1 if current_date.weekday() >= 5 else 0
        day_of_week = current_date.weekday()
        
        for product, popularity in products.items():
            # Random features
            stock = random.randint(10, 500)
            price = random.randint(50, 1000)
            
            # Realistic demand: (popularity * small multiplier) + small variance
            # For Sugar (8), this gives ~8-24 kg base
            base_demand = popularity * random.uniform(1.0, 3.0)
            
            # Weekend effect (scaled down)
            weekend_boost = random.uniform(2, 8) if is_weekend else 0
            
            # Combine with small noise
            demand = base_demand + weekend_boost + random.uniform(-2, 2)
            
            # Ensure integer and non-negative
            demand = max(1, int(round(demand)))
            
            data.append({
                "date": current_date,
                "product_name": product,
                "stock": stock,
                "price": price,
                "day_of_week": day_of_week,
                "is_weekend": is_weekend,
                "demand": demand
            })
            
        current_date += datetime.timedelta(days=1)
        
    df = pd.DataFrame(data)
    df.to_csv("ml/sales_data_6months.csv", index=False)
    print(f"Generated {len(df)} rows of realistic data in ml/sales_data_6months.csv")

if __name__ == "__main__":
    generate_6_months_data()
