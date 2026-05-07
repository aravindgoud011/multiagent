"""
Customer Dashboard — Bills, dues, payment history.
"""

from flask import Blueprint, jsonify, session
from ..extensions import get_db_connection
from ..models.bill import Bill
from ..models.payment import Payment
from ..models.user import User
from utils.helpers import login_required

customer_bp = Blueprint("customer", __name__)


@customer_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch User Info including loyalty points
    cursor.execute("SELECT id, name, phone, role, status, created_at, ISNULL(loyalty_points, 0) as loyalty_points FROM users WHERE id = ?", user_id)
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"error": "User not found"}), 404
        
    user_data = {
        "id": user_row.id,
        "name": user_row.name,
        "phone": user_row.phone,
        "role": user_row.role,
        "status": user_row.status,
        "loyalty_points": user_row.loyalty_points
    }

    # 2. Calculate Stats
    # Total of ALL credit bills
    cursor.execute("SELECT ISNULL(SUM(final_amount), 0) FROM bill WHERE customer_id = ? AND bill_type = 'credit'", user_id)
    credit_total = cursor.fetchone()[0]
    
    # Total of ALL payments
    cursor.execute("SELECT ISNULL(SUM(amount), 0) FROM payment WHERE customer_id = ?", user_id)
    paid_total = cursor.fetchone()[0]
    
    # Recent Purchases (Last 10)
    cursor.execute("SELECT TOP 10 * FROM bill WHERE customer_id = ? ORDER BY created_at DESC", user_id)
    bills = []
    for row in cursor.fetchall():
        bills.append(Bill(id=row.id, customer_id=row.customer_id, total_amount=row.total_amount, discount=row.discount, final_amount=row.final_amount, status=row.status, created_at=row.created_at).to_dict())

    # Recent Payments (Last 10)
    cursor.execute("SELECT TOP 10 * FROM payment WHERE customer_id = ? ORDER BY created_at DESC", user_id)
    payments = []
    for row in cursor.fetchall():
        payments.append(Payment(id=row.id, customer_id=row.customer_id, amount=row.amount, payment_mode=row.payment_mode, note=row.note, created_at=row.created_at).to_dict())

    # 3. Calculate Due
    total_due = credit_total - paid_total
    if total_due < 0: total_due = 0

    conn.close()

    return jsonify({
        "customer": user_data,
        "stats": {
            "total_bills_count": len(bills),
            "total_purchased": round(credit_total, 2),
            "total_paid": round(paid_total, 2),
            "total_due": round(total_due, 2),
            "loyalty_points": user_row.loyalty_points
        },
        "recent_bills": bills,
        "recent_payments": payments
    }), 200

@customer_bp.route("/spending-insights", methods=["GET"])
@login_required
def spending_insights():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get last 6 months spending
    cursor.execute("""
        SELECT TOP 6 
            FORMAT(created_at, 'MMM yyyy') as MonthYear, 
            SUM(final_amount) as TotalAmount
        FROM bill
        WHERE customer_id = ?
        GROUP BY FORMAT(created_at, 'MMM yyyy'), YEAR(created_at), MONTH(created_at)
        ORDER BY YEAR(created_at) DESC, MONTH(created_at) DESC
    """, user_id)
    
    data = []
    for row in cursor.fetchall():
        data.append({"month": row.MonthYear, "amount": row.TotalAmount})
        
    conn.close()
    return jsonify({"spending": data[::-1]}), 200

@customer_bp.route("/tickets", methods=["GET", "POST"])
@login_required
def tickets():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        from flask import request as flask_request
        data = flask_request.get_json()
        title = data.get("title")
        description = data.get("description")
        category = data.get("category", "General")
        
        if not title or not description:
            conn.close()
            return jsonify({"error": "Title and Description are required"}), 400
            
        cursor.execute("""
            INSERT INTO support_ticket (customer_id, title, description, category, status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, title, description, category, 'Open'))
        conn.commit()
        conn.close()
        return jsonify({"message": "Support ticket created successfully"}), 201
        
    else:
        cursor.execute("SELECT * FROM support_ticket WHERE customer_id = ? ORDER BY created_at DESC", user_id)
        tickets = []
        for row in cursor.fetchall():
            tickets.append({
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "category": row.category,
                "status": row.status,
                "created_at": row.created_at.isoformat()
            })
        conn.close()
        return jsonify({"tickets": tickets}), 200


@customer_bp.route("/due/<int:customer_id>", methods=["GET"])
@login_required
def customer_due(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", customer_id)
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"error": "Customer not found"}), 404
        
    user = User(id=user_row.id, name=user_row.name, phone=user_row.phone, role=user_row.role, status=user_row.status, created_at=user_row.created_at)

    # Calculate total of ALL credit bills ever taken
    cursor.execute("SELECT SUM(final_amount) FROM bill WHERE customer_id = ? AND bill_type = 'credit'", customer_id)
    total_credit_bills = cursor.fetchone()[0] or 0.0
    
    # Calculate total of ALL payments ever made
    cursor.execute("SELECT SUM(amount) FROM payment WHERE customer_id = ?", customer_id)
    total_payments = cursor.fetchone()[0] or 0.0
    
    conn.close()
    
    net_balance = total_credit_bills - total_payments
    
    return jsonify({
        "customer": user.to_dict(),
        "total_credit_bills": round(total_credit_bills, 2),
        "total_payments": round(total_payments, 2),
        "net_balance": round(net_balance, 2),
        "is_advance": net_balance < 0,
        "absolute_balance": round(abs(net_balance), 2)
    }), 200
