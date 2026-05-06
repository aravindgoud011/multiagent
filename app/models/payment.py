"""
Payment model.
"""

class Payment:
    def __init__(self, id=None, customer_id=None, amount=0.0, payment_mode="cash", note=None, created_at=None):
        self.id = id
        self.customer_id = customer_id
        self.amount = amount
        self.payment_mode = payment_mode
        self.note = note
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "payment_mode": self.payment_mode,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
