"""
Bill and BillItem models.
"""

class Bill:
    def __init__(self, id=None, customer_id=None, total_amount=0.0, discount=0.0, final_amount=0.0, status="unpaid", created_at=None, items=None, customer_name=None, bill_type="instant"):
        self.id = id
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.bill_type = bill_type
        self.total_amount = total_amount
        self.discount = discount
        self.final_amount = final_amount
        self.status = status
        self.created_at = created_at
        self.items = items or []

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "bill_type": self.bill_type,
            "total_amount": self.total_amount,
            "discount": self.discount,
            "final_amount": self.final_amount,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [item.to_dict() for item in self.items] if self.items else []
        }

class BillItem:
    def __init__(self, id=None, bill_id=None, product_id=None, quantity=0, price_per_unit=0.0, subtotal=0.0):
        self.id = id
        self.bill_id = bill_id
        self.product_id = product_id
        self.quantity = quantity
        self.price_per_unit = price_per_unit
        self.subtotal = subtotal

    def to_dict(self):
        return {
            "id": self.id,
            "bill_id": self.bill_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price_per_unit": self.price_per_unit,
            "subtotal": self.subtotal,
        }
