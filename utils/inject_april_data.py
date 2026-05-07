import os
import pyodbc
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

def inject_historical_data():
    load_dotenv()
    
    server = os.environ.get("AZURE_SQL_SERVER")
    username = os.environ.get("AZURE_SQL_USER")
    password = os.environ.get("AZURE_SQL_PASSWORD")
    db_name = os.environ.get("AZURE_SQL_DBNAME")
    
    conn_str = (
        "Driver={SQL Server};"
        f"Server={server};"
        f"Database={db_name};"
        f"Uid={username};"
        f"Pwd={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("Connected to Azure SQL.")

        # 1. Add 5 New Products
        new_prods = [
            ("Organic Honey 500g", "Groceries", 350.0, 50, "pcs"),
            ("Basmati Rice 5kg", "Groceries", 650.0, 40, "pcs"),
            ("Digestive Biscuits", "Snacks", 45.0, 100, "pcs"),
            ("Hand Sanitizer 500ml", "Personal Care", 250.0, 30, "pcs"),
            ("Glass Cleaner", "Household", 120.0, 25, "pcs")
        ]
        for name, cat, price, stock, unit in new_prods:
            cursor.execute("SELECT id FROM product WHERE name = ?", name)
            if not cursor.fetchone():
                print(f"Adding product: {name}")
                cursor.execute(
                    "INSERT INTO product (name, category, price, stock, unit, low_stock_threshold) VALUES (?, ?, ?, ?, ?, 5)",
                    (name, cat, price, stock, unit)
                )

        # 2. Add 5 New Customers
        new_customers = [
            ("Amit Kumar", "9111111111"),
            ("Priya Singh", "9222222222"),
            ("Suresh Raina", "9333333333"),
            ("Meena Iyer", "9444444444"),
            ("Rahul Dravid", "9555555555")
        ]
        
        pwd_hash = generate_password_hash("password123")
        customer_ids = []
        
        for name, phone in new_customers:
            cursor.execute("SELECT id FROM users WHERE phone = ?", phone)
            existing = cursor.fetchone()
            if not existing:
                print(f"Adding customer: {name}")
                cursor.execute(
                    "INSERT INTO users (name, phone, password_hash, role, status, loyalty_points) VALUES (?, ?, ?, 'customer', 'approved', 100)",
                    (name, phone, pwd_hash)
                )
                cursor.execute("SELECT @@IDENTITY")
                customer_ids.append(cursor.fetchone()[0])
            else:
                customer_ids.append(existing[0])

        # Get some products for billing
        cursor.execute("SELECT id, price, name FROM product")
        products = cursor.fetchall()
        if not products:
            print("No products found to create bills.")
            return

        # 3. Generate April Data
        start_date = datetime(2026, 4, 1)
        
        # We'll create about 60 instant bills and 30 credit bills
        # Credit bills will be paid on April 30
        
        credit_bills_to_pay = [] # (bill_id, customer_id, amount)

        print("Generating April bills...")
        for day in range(30):
            current_day = start_date + timedelta(days=day)
            
            # Instant Bills (2 per day)
            for i in range(2):
                bill_date = current_day.replace(hour=random.randint(9, 20), minute=random.randint(0, 59))
                cust_name = f"Walk-in {random.randint(100, 999)}"
                
                # Insert Bill
                cursor.execute(
                    "INSERT INTO bill (customer_name, bill_type, total_amount, discount, final_amount, status, created_at) VALUES (?, 'instant', 0, 0, 0, 'paid', ?)",
                    (cust_name, bill_date)
                )
                cursor.execute("SELECT @@IDENTITY")
                bill_id = cursor.fetchone()[0]
                
                # Add items (1-3 items)
                total_amount = 0
                for _ in range(random.randint(1, 3)):
                    p = random.choice(products)
                    qty = random.randint(1, 5)
                    subtotal = p.price * qty
                    total_amount += subtotal
                    cursor.execute(
                        "INSERT INTO bill_item (bill_id, product_id, quantity, price_per_unit, subtotal) VALUES (?, ?, ?, ?, ?)",
                        (bill_id, p.id, qty, p.price, subtotal)
                    )
                
                cursor.execute("UPDATE bill SET total_amount = ?, final_amount = ? WHERE id = ?", (total_amount, total_amount, bill_id))
                
                # Add Payment
                cursor.execute(
                    "INSERT INTO payment (amount, payment_mode, note, created_at) VALUES (?, 'cash', ?, ?)",
                    (total_amount, f"Instant Bill #{bill_id}", bill_date)
                )

            # Credit Bills (1 per day)
            if day % 1 == 0: # Every day
                bill_date = current_day.replace(hour=random.randint(10, 18), minute=random.randint(0, 59))
                cust_id = random.choice(customer_ids)
                
                # Insert Bill (status: paid as requested "credit customer bills should be paid at april 30")
                # Wait, they are created as UNPAID first, then paid on April 30.
                cursor.execute(
                    "INSERT INTO bill (customer_id, bill_type, total_amount, discount, final_amount, status, created_at) VALUES (?, 'credit', 0, 0, 0, 'paid', ?)",
                    (cust_id, bill_date)
                )
                cursor.execute("SELECT @@IDENTITY")
                bill_id = cursor.fetchone()[0]
                
                total_amount = 0
                for _ in range(random.randint(2, 4)):
                    p = random.choice(products)
                    qty = random.randint(1, 3)
                    subtotal = p.price * qty
                    total_amount += subtotal
                    cursor.execute(
                        "INSERT INTO bill_item (bill_id, product_id, quantity, price_per_unit, subtotal) VALUES (?, ?, ?, ?, ?)",
                        (bill_id, p.id, qty, p.price, subtotal)
                    )
                
                cursor.execute("UPDATE bill SET total_amount = ?, final_amount = ? WHERE id = ?", (total_amount, total_amount, bill_id))
                credit_bills_to_pay.append((bill_id, cust_id, total_amount))

        # 4. Add Payments for Credit Bills on April 30
        pay_date = datetime(2026, 4, 30, 18, 0, 0)
        print("Recording credit payments on April 30...")
        for b_id, c_id, amt in credit_bills_to_pay:
            cursor.execute(
                "INSERT INTO payment (customer_id, amount, payment_mode, note, created_at) VALUES (?, ?, 'cash', ?, ?)",
                (c_id, amt, f"Credit Clear for Bill #{b_id}", pay_date)
            )

        conn.commit()
        print("Successfully injected April data!")
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inject_historical_data()
