"""
Bill and BillItem models — supports Instant and Credit billing.
"""

from datetime import datetime
from ..extensions import db


class Bill(db.Model):
    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bill_type = db.Column(db.String(10), nullable=False)  # "instant" or "credit"
    payment_mode = db.Column(db.String(10), nullable=True)  # "cash" / "upi" (for instant bills)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    is_paid = db.Column(db.Boolean, default=False)  # relevant for credit bills
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---
    items = db.relationship("BillItem", backref="bill", lazy=True, cascade="all, delete-orphan")

    def calculate_total(self):
        """Recalculate total from line items."""
        self.total_amount = sum(item.subtotal for item in self.items)

    def to_dict(self):
        """Return a JSON-safe dictionary including line items."""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "bill_type": self.bill_type,
            "payment_mode": self.payment_mode,
            "total_amount": self.total_amount,
            "is_paid": self.is_paid,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items],
        }

    def __repr__(self):
        return f"<Bill #{self.id} — ₹{self.total_amount} ({self.bill_type})>"


class BillItem(db.Model):
    __tablename__ = "bill_items"

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)   # snapshot at billing time
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal,
        }

    def __repr__(self):
        return f"<BillItem {self.product_name} x{self.quantity}>"
