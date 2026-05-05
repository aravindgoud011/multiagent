"""
Payments — Record payments against customer credit.
"""

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.payment import Payment
from ..models.user import User
from ..utils.helpers import admin_required, login_required

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/record", methods=["POST"])
@admin_required
def record_payment():
    """
    Record a payment.

    JSON body:
    {
        "customer_id": 2,
        "amount": 500.00,
        "payment_mode": "cash",
        "note": "May month partial payment"
    }
    """
    data = request.get_json()
    customer_id = data.get("customer_id")
    amount = data.get("amount")
    payment_mode = data.get("payment_mode", "cash").lower()

    if not customer_id or not amount:
        return jsonify({"error": "customer_id and amount are required"}), 400

    if float(amount) <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    customer = User.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    payment = Payment(
        customer_id=customer_id,
        amount=float(amount),
        payment_mode=payment_mode,
        note=data.get("note", "").strip() or None,
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({"message": "Payment recorded", "payment": payment.to_dict()}), 201


@payments_bp.route("/pay", methods=["POST"])
@login_required
def customer_pay():
    """Customer initiates a payment."""
    from flask import session
    customer_id = session.get("user_id")
    data = request.get_json()
    amount = data.get("amount")
    payment_mode = data.get("payment_mode", "upi").lower()

    if not amount or float(amount) <= 0:
        return jsonify({"error": "Valid amount is required"}), 400

    payment = Payment(
        customer_id=customer_id,
        amount=float(amount),
        payment_mode=payment_mode,
        note="Customer initiated payment",
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({"message": "Payment successful", "payment": payment.to_dict()}), 201


@payments_bp.route("/all", methods=["GET"])
@admin_required
def all_payments():
    """Get all payments (admin view)."""
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    return jsonify({"count": len(payments), "payments": [p.to_dict() for p in payments]}), 200


@payments_bp.route("/customer/<int:customer_id>", methods=["GET"])
@admin_required
def customer_payments(customer_id):
    """Get payment history for a customer."""
    payments = Payment.query.filter_by(customer_id=customer_id).order_by(Payment.created_at.desc()).all()
    return jsonify({"count": len(payments), "payments": [p.to_dict() for p in payments]}), 200
