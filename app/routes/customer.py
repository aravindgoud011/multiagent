"""
Customer Dashboard — Bills, dues, payment history.
"""

from flask import Blueprint, jsonify, session
from ..extensions import get_db_connection
from ..models.bill import Bill
from ..models.payment import Payment
from ..models.user import User
from ..utils.helpers import login_required

customer_bp = Blueprint("customer", __name__)


@customer_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", user_id)
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"error": "User not found"}), 404
        
    user = User(id=user_row.id, name=user_row.name, phone=user_row.phone, role=user_row.role, status=user_row.status, created_at=user_row.created_at)

    cursor.execute("SELECT * FROM bill WHERE customer_id = ? ORDER BY created_at DESC", user_id)
    bills = []
    credit_total = 0.0
    for row in cursor.fetchall():
        b = Bill(id=row.id, customer_id=row.customer_id, total_amount=row.total_amount, discount=row.discount, final_amount=row.final_amount, status=row.status, created_at=row.created_at)
        bills.append(b)
        if b.status == "unpaid":
            credit_total += b.total_amount

    cursor.execute("SELECT * FROM payment WHERE customer_id = ? ORDER BY created_at DESC", user_id)
    payments = []
    paid_total = 0.0
    for row in cursor.fetchall():
        p = Payment(id=row.id, customer_id=row.customer_id, amount=row.amount, payment_mode=row.payment_mode, note=row.note, created_at=row.created_at)
        payments.append(p)
        paid_total += p.amount

    conn.close()

    total_due = credit_total - paid_total
    if total_due < 0:
        total_due = 0

    return jsonify({
        "customer": user.to_dict(),
        "total_bills": len(bills),
        "credit_total": round(credit_total, 2),
        "paid_total": round(paid_total, 2),
        "total_due": round(total_due, 2),
        "bills": [b.to_dict() for b in bills],
        "payments": [p.to_dict() for p in payments],
    }), 200


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

    cursor.execute("SELECT SUM(total_amount) FROM bill WHERE customer_id = ? AND status = 'unpaid'", customer_id)
    credit_total = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(amount) FROM payment WHERE customer_id = ?", customer_id)
    paid_total = cursor.fetchone()[0] or 0.0

    conn.close()

    total_due = credit_total - paid_total
    if total_due < 0:
        total_due = 0

    return jsonify({
        "customer": user.to_dict(),
        "credit_total": round(credit_total, 2),
        "paid_total": round(paid_total, 2),
        "total_due": round(total_due, 2),
    }), 200
