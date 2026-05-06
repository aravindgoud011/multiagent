"""
Billing — Create bills (instant / credit).
"""

from flask import Blueprint, request, jsonify, session
from ..extensions import get_db_connection
from ..models.bill import Bill, BillItem
from ..models.product import Product
from ..models.user import User
from ..utils.helpers import login_required, admin_required

billing_bp = Blueprint("billing", __name__)


@billing_bp.route("/create", methods=["POST"])
@admin_required
def create_bill():
    data = request.get_json()
    bill_type = data.get("bill_type", "instant").lower()
    items_data = data.get("items", [])
    
    customer_id = data.get("customer_id")
    customer_name = data.get("customer_name")

    if not items_data:
        return jsonify({"error": "items are required"}), 400

    if bill_type not in ("instant", "credit"):
        return jsonify({"error": "bill_type must be instant or credit"}), 400
        
    if bill_type == "credit" and not customer_id:
        return jsonify({"error": "customer_id is required for credit bills"}), 400
        
    if bill_type == "instant" and not customer_name:
        return jsonify({"error": "customer_name is required for instant bills"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if customer_id:
        cursor.execute("SELECT id FROM users WHERE id = ?", customer_id)
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Customer not found"}), 404

    status = "paid" if bill_type == "instant" else "unpaid"

    cursor.execute(
        "INSERT INTO bill (customer_id, customer_name, bill_type, total_amount, discount, final_amount, status) VALUES (?, ?, ?, 0, 0, 0, ?)",
        (customer_id, customer_name, bill_type, status)
    )
    cursor.execute("SELECT @@IDENTITY AS id")
    bill_id = cursor.fetchone()[0]

    total = 0.0
    try:
        for item_data in items_data:
            product_id = item_data.get("product_id")
            qty = int(item_data.get("quantity", 1))
            
            cursor.execute("SELECT id, name, price, stock FROM product WHERE id = ?", product_id)
            p_row = cursor.fetchone()
            
            if not p_row:
                conn.rollback()
                conn.close()
                return jsonify({"error": f"Product ID {product_id} not found"}), 404
                
            if p_row.stock < qty:
                conn.rollback()
                conn.close()
                return jsonify({"error": f"Not enough stock for {p_row.name} (available: {p_row.stock})"}), 400

            subtotal = p_row.price * qty
            total += subtotal

            cursor.execute(
                "INSERT INTO bill_item (bill_id, product_id, quantity, price_per_unit, subtotal) VALUES (?, ?, ?, ?, ?)",
                (bill_id, product_id, qty, p_row.price, subtotal)
            )
            
            cursor.execute("UPDATE product SET stock = stock - ? WHERE id = ?", (qty, product_id))
            
            # Low Stock Check
            cursor.execute("SELECT stock, low_stock_threshold FROM product WHERE id = ?", product_id)
            stock_row = cursor.fetchone()
            if stock_row and stock_row.stock <= stock_row.low_stock_threshold:
                cursor.execute(
                    "INSERT INTO notification (title, message) VALUES (?, ?)",
                    ("Low Stock Alert", f"Product '{p_row.name}' is low on stock! Remaining: {stock_row.stock}")
                )

        cursor.execute("UPDATE bill SET total_amount = ?, final_amount = ? WHERE id = ?", (total, total, bill_id))
        
        if bill_type == "instant":
            payment_mode = data.get("payment_mode", "cash")
            cursor.execute("INSERT INTO payment (customer_id, amount, payment_mode, note) VALUES (?, ?, ?, ?)",
                           (customer_id, total, payment_mode, f"Instant Bill #{bill_id}"))
                           
        conn.commit()

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cursor.execute("SELECT * FROM bill WHERE id = ?", bill_id)
    b_row = cursor.fetchone()
    conn.close()
    
    bill = Bill(id=b_row.id, customer_id=b_row.customer_id, customer_name=b_row.customer_name, bill_type=b_row.bill_type, total_amount=b_row.total_amount, final_amount=b_row.final_amount, status=b_row.status, created_at=b_row.created_at)
    return jsonify({"message": "Bill created", "bill": bill.to_dict()}), 201

@billing_bp.route("/dashboard_stats", methods=["GET"])
@admin_required
def dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Revenue (Total of all payments received)
    cursor.execute("SELECT SUM(amount) FROM payment")
    revenue = cursor.fetchone()[0] or 0.0
    
    # Bills Pending (Count of unpaid bills)
    cursor.execute("SELECT COUNT(id) FROM bill WHERE status = 'unpaid'")
    pending_bills = cursor.fetchone()[0] or 0
    
    # Low Stock Items
    cursor.execute("SELECT COUNT(id) FROM product WHERE stock <= low_stock_threshold")
    low_stock = cursor.fetchone()[0] or 0
    
    # Total Customers
    cursor.execute("SELECT COUNT(id) FROM users WHERE role = 'customer' AND status = 'approved'")
    customers_count = cursor.fetchone()[0] or 0
    
    # Pie Chart Data (Sales by category)
    cursor.execute("""
        SELECT p.category, SUM(bi.subtotal) 
        FROM bill_item bi
        JOIN product p ON bi.product_id = p.id
        JOIN bill b ON bi.bill_id = b.id
        GROUP BY p.category
    """)
    sales_data = [{"category": row[0] or "Other", "sales": row[1]} for row in cursor.fetchall()]

    # Sales Trend (Line Chart - Last 7 Days)
    # Note: SQL Server specific query for date grouping
    cursor.execute("""
        SELECT CAST(created_at AS DATE) as date, SUM(amount) as total
        FROM payment
        WHERE created_at >= DATEADD(day, -7, GETUTCDATE())
        GROUP BY CAST(created_at AS DATE)
        ORDER BY date
    """)
    trend_rows = cursor.fetchall()
    sales_trend = [{"date": str(row[0]), "total": row[1]} for row in trend_rows]

    # Low Stock Items List
    cursor.execute("SELECT id, name, stock, low_stock_threshold FROM product WHERE stock <= low_stock_threshold")
    low_stock_list = []
    for row in cursor.fetchall():
        low_stock_list.append({
            "id": row.id,
            "name": row.name,
            "stock": row.stock,
            "threshold": row.low_stock_threshold,
            "status": "Critical" if row.stock <= 5 else "Warning"
        })

    # Recent Alerts (Latest 5 notifications)
    cursor.execute("SELECT TOP 5 title, message, created_at FROM notification ORDER BY created_at DESC")
    alerts = [{"title": row.title, "message": row.message, "time": row.created_at.isoformat()} for row in cursor.fetchall()]

    conn.close()
    
    return jsonify({
        "revenue": revenue,
        "pending_bills": pending_bills,
        "low_stock": low_stock,
        "customers_count": customers_count,
        "sales_data": sales_data,
        "sales_trend": sales_trend,
        "low_stock_list": low_stock_list,
        "alerts": alerts
    }), 200



@billing_bp.route("/all", methods=["GET"])
@admin_required
def all_bills():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bill ORDER BY created_at DESC")
    bills = []
    for row in cursor.fetchall():
        bills.append(Bill(id=row.id, customer_id=row.customer_id, customer_name=row.customer_name, bill_type=row.bill_type, total_amount=row.total_amount, final_amount=row.final_amount, status=row.status, created_at=row.created_at))
    conn.close()
    return jsonify({"count": len(bills), "bills": [b.to_dict() for b in bills]}), 200


@billing_bp.route("/<int:bill_id>", methods=["GET"])
@login_required
def get_bill(bill_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bill WHERE id = ?", bill_id)
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Bill not found"}), 404
        
    bill = Bill(id=row.id, customer_id=row.customer_id, customer_name=row.customer_name, bill_type=row.bill_type, total_amount=row.total_amount, final_amount=row.final_amount, status=row.status, created_at=row.created_at)
    
    cursor.execute("""
        SELECT bi.*, p.name as product_name 
        FROM bill_item bi 
        LEFT JOIN product p ON bi.product_id = p.id 
        WHERE bi.bill_id = ?
    """, bill_id)
    
    items_data = []
    for i_row in cursor.fetchall():
        item_dict = {
            "id": i_row.id,
            "bill_id": i_row.bill_id,
            "product_id": i_row.product_id,
            "product_name": getattr(i_row, 'product_name', f'Product #{i_row.product_id}'),
            "quantity": i_row.quantity,
            "price_per_unit": i_row.price_per_unit,
            "subtotal": i_row.subtotal
        }
        items_data.append(item_dict)
        
    conn.close()
    
    bill_dict = bill.to_dict()
    bill_dict["items"] = items_data
    return jsonify({"bill": bill_dict}), 200


@billing_bp.route("/customer/<int:customer_id>", methods=["GET"])
@login_required
def customer_bills(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bill WHERE customer_id = ? ORDER BY created_at DESC", customer_id)
    bills = []
    for row in cursor.fetchall():
        bills.append(Bill(id=row.id, customer_id=row.customer_id, customer_name=row.customer_name, bill_type=row.bill_type, total_amount=row.total_amount, final_amount=row.final_amount, status=row.status, created_at=row.created_at))
    conn.close()
    return jsonify({"count": len(bills), "bills": [b.to_dict() for b in bills]}), 200


@billing_bp.route("/customers", methods=["GET"])
@admin_required
def list_customers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role = 'customer' ORDER BY name")
    customers = []
    for row in cursor.fetchall():
        customers.append(User(id=row.id, name=row.name, phone=row.phone, role=row.role, status=row.status, created_at=row.created_at))
    conn.close()
    return jsonify({"customers": [c.to_dict() for c in customers]}), 200


@billing_bp.route("/customers/pending", methods=["GET"])
@admin_required
def list_pending_customers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role = 'customer' AND status = 'pending' ORDER BY name")
    customers = []
    for row in cursor.fetchall():
        customers.append(User(id=row.id, name=row.name, phone=row.phone, role=row.role, status=row.status, created_at=row.created_at))
    conn.close()
    return jsonify({"customers": [c.to_dict() for c in customers]}), 200


@billing_bp.route("/customers/<int:user_id>/approve", methods=["POST"])
@admin_required
def approve_customer(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ?", user_id)
    row = cursor.fetchone()
    if not row or row.role != "customer":
        conn.close()
        return jsonify({"error": "Customer not found"}), 404
        
    cursor.execute("UPDATE users SET status = 'approved' WHERE id = ?", user_id)
    conn.commit()
    conn.close()
    return jsonify({"message": "Customer approved"}), 200


@billing_bp.route("/customers/<int:user_id>/reject", methods=["POST"])
@admin_required
def reject_customer(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ?", user_id)
    row = cursor.fetchone()
    if not row or row.role != "customer":
        conn.close()
        return jsonify({"error": "Customer not found"}), 404
        
    cursor.execute("DELETE FROM users WHERE id = ?", user_id)
    conn.commit()
    conn.close()
    return jsonify({"message": "Customer rejected"}), 200
@billing_bp.route("/receipt/<int:bill_id>", methods=["GET"])
def get_receipt(bill_id):
    """Fetch full bill details and items for receipt/invoice."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Get Bill Header
    cursor.execute("SELECT * FROM bill WHERE id = ?", bill_id)
    b_row = cursor.fetchone()
    if not b_row:
        conn.close()
        return jsonify({"error": "Bill not found"}), 404
        
    bill = Bill(id=b_row.id, customer_id=b_row.customer_id, customer_name=b_row.customer_name, bill_type=b_row.bill_type, total_amount=b_row.total_amount, final_amount=b_row.final_amount, status=b_row.status, created_at=b_row.created_at)
    
    # 2. Get Bill Items
    cursor.execute("""
        SELECT bi.*, p.name as product_name 
        FROM bill_item bi
        JOIN product p ON bi.product_id = p.id
        WHERE bi.bill_id = ?
    """, bill_id)
    
    items = []
    for row in cursor.fetchall():
        items.append({
            "product_name": row.product_name,
            "quantity": row.quantity,
            "price_per_unit": row.price_per_unit,
            "subtotal": row.subtotal
        })
        
    conn.close()
    return jsonify({
        "bill": bill.to_dict(),
        "items": items
    }), 200
