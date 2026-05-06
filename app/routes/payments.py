"""
Payments — Record payments against customer credit.
"""

from flask import Blueprint, request, jsonify, session
from ..extensions import get_db_connection
from ..models.payment import Payment
from ..models.user import User
from ..utils.helpers import admin_required, login_required

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/record", methods=["POST"])
@admin_required
def record_payment():
    data = request.get_json()
    customer_id = data.get("customer_id")
    amount = data.get("amount")
    payment_mode = data.get("payment_mode", "cash").lower()

    if not customer_id or not amount:
        return jsonify({"error": "customer_id and amount are required"}), 400

    if float(amount) <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE id = ?", customer_id)
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Customer not found"}), 404

    note = data.get("note", "").strip() or None
    cursor.execute(
        "INSERT INTO payment (customer_id, amount, payment_mode, note) VALUES (?, ?, ?, ?)",
        (customer_id, float(amount), payment_mode, note)
    )

    # Automatically mark oldest unpaid bills as paid using the payment amount
    amount_left = float(amount)
    cursor.execute("SELECT id, final_amount FROM bill WHERE customer_id = ? AND status = 'unpaid' ORDER BY created_at ASC", customer_id)
    for ub in cursor.fetchall():
        if amount_left >= ub.final_amount:
            cursor.execute("UPDATE bill SET status = 'paid' WHERE id = ?", ub.id)
            amount_left -= ub.final_amount
        else:
            break

    conn.commit()
    
    cursor.execute("SELECT @@IDENTITY AS id")
    payment_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM payment WHERE id = ?", payment_id)
    row = cursor.fetchone()
    conn.close()

    payment = Payment(id=row.id, customer_id=row.customer_id, amount=row.amount, payment_mode=row.payment_mode, note=row.note, created_at=row.created_at)

    return jsonify({"message": "Payment recorded", "payment": payment.to_dict()}), 201


@payments_bp.route("/pay", methods=["POST"])
@login_required
def customer_pay():
    customer_id = session.get("user_id")
    data = request.get_json()
    amount = data.get("amount")
    payment_mode = data.get("payment_mode", "upi").lower()

    if not amount or float(amount) <= 0:
        return jsonify({"error": "Valid amount is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    note = "Customer initiated payment"
    cursor.execute(
        "INSERT INTO payment (customer_id, amount, payment_mode, note) VALUES (?, ?, ?, ?)",
        (customer_id, float(amount), payment_mode, note)
    )

    amount_left = float(amount)
    cursor.execute("SELECT id, final_amount FROM bill WHERE customer_id = ? AND status = 'unpaid' ORDER BY created_at ASC", customer_id)
    for ub in cursor.fetchall():
        if amount_left >= ub.final_amount:
            cursor.execute("UPDATE bill SET status = 'paid' WHERE id = ?", ub.id)
            amount_left -= ub.final_amount
        else:
            break

    conn.commit()
    
    cursor.execute("SELECT @@IDENTITY AS id")
    payment_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM payment WHERE id = ?", payment_id)
    row = cursor.fetchone()
    conn.close()

    payment = Payment(id=row.id, customer_id=row.customer_id, amount=row.amount, payment_mode=row.payment_mode, note=row.note, created_at=row.created_at)

    return jsonify({"message": "Payment successful", "payment": payment.to_dict()}), 201


@payments_bp.route("/all", methods=["GET"])
@admin_required
def all_payments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payment ORDER BY created_at DESC")
    
    payments = []
    for row in cursor.fetchall():
        p = Payment(id=row.id, customer_id=row.customer_id, amount=row.amount, payment_mode=row.payment_mode, note=row.note, created_at=row.created_at)
        payments.append(p)
        
    conn.close()
    return jsonify({"count": len(payments), "payments": [p.to_dict() for p in payments]}), 200


@payments_bp.route("/customer/<int:customer_id>", methods=["GET"])
@admin_required
def customer_payments(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payment WHERE customer_id = ? ORDER BY created_at DESC", customer_id)
    
    payments = []
    for row in cursor.fetchall():
        p = Payment(id=row.id, customer_id=row.customer_id, amount=row.amount, payment_mode=row.payment_mode, note=row.note, created_at=row.created_at)
        payments.append(p)
        
    conn.close()
    return jsonify({"count": len(payments), "payments": [p.to_dict() for p in payments]}), 200
