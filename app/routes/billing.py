"""
Billing — Create bills (instant / credit).
"""

from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models.bill import Bill, BillItem
from ..models.product import Product
from ..models.user import User
from ..utils.helpers import login_required, admin_required

billing_bp = Blueprint("billing", __name__)


@billing_bp.route("/create", methods=["POST"])
@admin_required
def create_bill():
    """
    Create a bill.

    JSON body:
    {
        "customer_id": 2,
        "bill_type": "instant",       // "instant" or "credit"
        "payment_mode": "cash",       // "cash" or "upi" (for instant)
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 3, "quantity": 1}
        ]
    }
    """
    data = request.get_json()
    customer_id = data.get("customer_id")
    bill_type = data.get("bill_type", "instant").lower()
    payment_mode = data.get("payment_mode")
    items_data = data.get("items", [])

    if not customer_id or not items_data:
        return jsonify({"error": "customer_id and items are required"}), 400

    if bill_type not in ("instant", "credit"):
        return jsonify({"error": "bill_type must be instant or credit"}), 400

    customer = User.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # Create bill
    bill = Bill(
        customer_id=customer_id,
        bill_type=bill_type,
        payment_mode=payment_mode if bill_type == "instant" else None,
        is_paid=(bill_type == "instant"),
    )
    db.session.add(bill)

    # Add items
    total = 0.0
    for item_data in items_data:
        product = Product.query.get(item_data.get("product_id"))
        if not product:
            db.session.rollback()
            return jsonify({"error": f"Product ID {item_data.get('product_id')} not found"}), 404

        qty = int(item_data.get("quantity", 1))
        if product.stock < qty:
            db.session.rollback()
            return jsonify({"error": f"Not enough stock for {product.name} (available: {product.stock})"}), 400

        subtotal = product.price * qty
        total += subtotal

        bill_item = BillItem(
            bill=bill,
            product_id=product.id,
            product_name=product.name,
            quantity=qty,
            unit_price=product.price,
            subtotal=subtotal,
        )
        db.session.add(bill_item)

        # Reduce stock
        product.stock -= qty

    bill.total_amount = total
    db.session.commit()

    return jsonify({"message": "Bill created", "bill": bill.to_dict()}), 201


@billing_bp.route("/all", methods=["GET"])
@admin_required
def all_bills():
    """Get all bills (admin view)."""
    bills = Bill.query.order_by(Bill.created_at.desc()).all()
    return jsonify({"count": len(bills), "bills": [b.to_dict() for b in bills]}), 200


@billing_bp.route("/<int:bill_id>", methods=["GET"])
@login_required
def get_bill(bill_id):
    """Get a single bill."""
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify({"error": "Bill not found"}), 404
    return jsonify({"bill": bill.to_dict()}), 200


@billing_bp.route("/customer/<int:customer_id>", methods=["GET"])
@login_required
def customer_bills(customer_id):
    """Get all bills for a customer."""
    bills = Bill.query.filter_by(customer_id=customer_id).order_by(Bill.created_at.desc()).all()
    return jsonify({"count": len(bills), "bills": [b.to_dict() for b in bills]}), 200


@billing_bp.route("/customers", methods=["GET"])
@admin_required
def list_customers():
    """List all customers (for billing dropdown)."""
    customers = User.query.filter_by(role="customer", status="approved").order_by(User.name).all()
    return jsonify({"customers": [c.to_dict() for c in customers]}), 200


@billing_bp.route("/customers/pending", methods=["GET"])
@admin_required
def list_pending_customers():
    """List all pending customers."""
    customers = User.query.filter_by(role="customer", status="pending").order_by(User.name).all()
    return jsonify({"customers": [c.to_dict() for c in customers]}), 200

@billing_bp.route("/customers/<int:user_id>/approve", methods=["POST"])
@admin_required
def approve_customer(user_id):
    """Approve a customer."""
    customer = User.query.get(user_id)
    if not customer or customer.role != "customer":
        return jsonify({"error": "Customer not found"}), 404
    customer.status = "approved"
    db.session.commit()
    return jsonify({"message": "Customer approved"}), 200

@billing_bp.route("/customers/<int:user_id>/reject", methods=["POST"])
@admin_required
def reject_customer(user_id):
    """Reject (delete) a customer."""
    customer = User.query.get(user_id)
    if not customer or customer.role != "customer":
        return jsonify({"error": "Customer not found"}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer rejected"}), 200
