"""
Product model — Inventory items for the Kirana store.
"""

from datetime import datetime
from ..extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=True)       # e.g. "Grocery", "Dairy"
    price = db.Column(db.Float, nullable=False)               # selling price per unit
    stock = db.Column(db.Integer, nullable=False, default=0)  # current quantity
    low_stock_threshold = db.Column(db.Integer, default=10)   # alert when stock <= this
    unit = db.Column(db.String(20), default="pcs")            # "kg", "litre", "pcs"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_low_stock(self):
        """Return True if current stock is at or below the threshold."""
        return self.stock <= self.low_stock_threshold

    def to_dict(self):
        """Return a JSON-safe dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "stock": self.stock,
            "unit": self.unit,
            "low_stock_threshold": self.low_stock_threshold,
            "is_low_stock": self.is_low_stock,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Product {self.name} — stock: {self.stock}>"
