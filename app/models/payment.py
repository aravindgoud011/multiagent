"""
Payment model — Records cash/UPI payments against a customer's credit.
"""

from datetime import datetime
from ..extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.String(10), nullable=False)  # "cash" or "upi"
    note = db.Column(db.String(255), nullable=True)           # optional remark
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "payment_mode": self.payment_mode,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Payment ₹{self.amount} by Customer #{self.customer_id}>"
