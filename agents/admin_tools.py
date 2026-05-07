import os
import datetime
import pandas as pd
from app.backend.extensions import get_db_connection
from rag.engine import rag_engine

def query_inventory(query: str):
    """Search for products using RAG and database lookup."""
    # 1. RAG search for semantic matches
    try:
        rag_docs = rag_engine.search(query, k=3)
        rag_context = "\n".join([doc.page_content for doc in rag_docs])
    except Exception as e:
        print(f"RAG Search Error: {e}")
        rag_context = "RAG search unavailable."
    
    # 2. SQL lookup for exact/partial name matches
    conn = get_db_connection()
    try:
        df = pd.read_sql(f"SELECT name, category, price, stock, unit FROM product WHERE name LIKE ?", conn, params=[f"%{query}%"])
        sql_context = df.to_string(index=False) if not df.empty else "No direct database matches found."
    finally:
        conn.close()
        
    return f"RAG Context:\n{rag_context}\n\nDatabase Matches:\n{sql_context}"

def add_product(name: str, category: str, price: float, stock: int, unit: str = 'pcs'):
    """Add a new product to the inventory."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO product (name, category, price, stock, unit, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            name, category, price, stock, unit, datetime.datetime.utcnow(), datetime.datetime.utcnow()
        )
        conn.commit()
        return f"Successfully added {name} to inventory."
    except Exception as e:
        return f"Error adding product: {e}"
    finally:
        conn.close()

def update_stock(product_name: str, stock_change: int):
    """Update stock for an existing product (can be positive or negative)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Find product
        cursor.execute("SELECT id, name, stock FROM product WHERE name LIKE ?", f"%{product_name}%")
        row = cursor.fetchone()
        if not row:
            return f"Product '{product_name}' not found."
        
        new_stock = max(0, row.stock + stock_change)
        cursor.execute(
            "UPDATE product SET stock = ?, updated_at = ? WHERE id = ?",
            new_stock, datetime.datetime.utcnow(), row.id
        )
        conn.commit()
        return f"Updated stock for {row.name}. New stock: {new_stock} (Previous: {row.stock})"
    except Exception as e:
        return f"Error updating stock: {e}"
    finally:
        conn.close()

def get_sales_report(days: int = 7):
    """Get general sales summary for the last X days."""
    conn = get_db_connection()
    try:
        query = """
        SELECT CAST(created_at AS DATE) as date, SUM(final_amount) as total_revenue, COUNT(*) as bill_count
        FROM bill
        WHERE created_at >= DATEADD(day, -?, GETDATE())
        GROUP BY CAST(created_at AS DATE)
        ORDER BY date DESC
        """
        df = pd.read_sql(query, conn, params=[days])
        return df.to_string(index=False) if not df.empty else "No general sales data found."
    except Exception as e:
        return f"Database error fetching sales: {str(e)[:100]}"
    finally:
        conn.close()

def get_product_sales(product_name: str):
    """Get sales data for a specific product by joining bill_item and product tables."""
    conn = get_db_connection()
    try:
        query = """
        SELECT p.name, SUM(bi.quantity) as total_qty, SUM(bi.subtotal) as total_revenue
        FROM bill_item bi
        JOIN product p ON bi.product_id = p.id
        WHERE p.name LIKE ?
        GROUP BY p.name
        """
        df = pd.read_sql(query, conn, params=[f"%{product_name}%"])
        return df.to_string(index=False) if not df.empty else f"No sales records found for product: {product_name}"
    except Exception as e:
        return f"Database error fetching product sales: {str(e)[:100]}"
    finally:
        conn.close()

def get_customer_requests():
    """Get recent customer requests and notifications."""
    conn = get_db_connection()
    try:
        # Fetch notifications which often represent customer interest
        df = pd.read_sql("SELECT TOP 10 title, message, created_at FROM notification ORDER BY created_at DESC", conn)
        return df.to_string(index=False) if not df.empty else "No customer requests found."
    finally:
        conn.close()

def get_payments(limit: int = 10):
    """Get recent payment history."""
    conn = get_db_connection()
    try:
        df = pd.read_sql(f"SELECT TOP {limit} customer_id, amount, payment_mode, created_at FROM payment ORDER BY created_at DESC", conn)
        return df.to_string(index=False) if not df.empty else "No payment data found."
    finally:
        conn.close()

def get_top_selling_products(limit: int = 5):
    """Get the top selling products by total quantity sold."""
    conn = get_db_connection()
    try:
        query = f"""
        SELECT TOP {limit} p.name, SUM(bi.quantity) as total_sold, SUM(bi.subtotal) as total_revenue
        FROM bill_item bi
        JOIN product p ON bi.product_id = p.id
        GROUP BY p.name
        ORDER BY total_sold DESC
        """
        df = pd.read_sql(query, conn)
        return df.to_string(index=False) if not df.empty else "No sales records found."
    except Exception as e:
        return f"Database error fetching top products: {str(e)[:100]}"
    finally:
        conn.close()
