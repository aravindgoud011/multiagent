import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle
import os

def train_local_model():
    # 1. Load data
    csv_path = "ml/sales_data_6months.csv"
    if not os.path.exists(csv_path):
        print("Data file not found. Run generate_data.py first.")
        return
        
    df = pd.read_csv(csv_path)
    
    # 2. Preprocessing
    le = LabelEncoder()
    df['product_encoded'] = le.fit_transform(df['product_name'])
    
    # Select features and target
    features = ['product_encoded', 'stock', 'price', 'day_of_week', 'is_weekend']
    X = df[features]
    y = df['demand']
    
    # 3. Train model (Switching to RandomForest for better non-linear patterns)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 4. Save model and label encoder
    model_data = {
        "model": model,
        "label_encoder": le,
        "features": features
    }
    
    with open("ml/model.pkl", "wb") as f:
        pickle.dump(model_data, f)
        
    print("Model trained and saved to ml/model.pkl")
    print(f"Model Score (R^2): {model.score(X_test, y_test):.4f}")

if __name__ == "__main__":
    train_local_model()
