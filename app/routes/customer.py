"""
Customer Dashboard — Bills, dues, payment history.
"""

from flask import Blueprint, jsonify, session
from ..models.bill import Bill
from ..models.payment import Payment
from ..models.user import User
from ..utils.helpers import login_required

customer_bp = Blueprint("customer", __name__)


@customer_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """Get dashboard data for the logged-in customer."""
    user_id = session["user_id"]
    user = User.query.get(user_id)

    # All bills
    bills = Bill.query.filter_by(customer_id=user_id).order_by(Bill.created_at.desc()).all()

    # Credit bills total
    credit_total = sum(b.total_amount for b in bills if b.bill_type == "credit")

    # Payments total
    payments = Payment.query.filter_by(customer_id=user_id).order_by(Payment.created_at.desc()).all()
    paid_total = sum(p.amount for p in payments)

    # Due = credit bills - payments
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
    """Calculate total due for a specific customer."""
    user = User.query.get(customer_id)
    if not user:
        return jsonify({"error": "Customer not found"}), 404

    credit_bills = Bill.query.filter_by(customer_id=customer_id, bill_type="credit").all()
    credit_total = sum(b.total_amount for b in credit_bills)

    payments = Payment.query.filter_by(customer_id=customer_id).all()
    paid_total = sum(p.amount for p in payments)

    total_due = credit_total - paid_total
    if total_due < 0:
        total_due = 0

    return jsonify({
        "customer": user.to_dict(),
        "credit_total": round(credit_total, 2),
        "paid_total": round(paid_total, 2),
        "total_due": round(total_due, 2),
    }), 200
