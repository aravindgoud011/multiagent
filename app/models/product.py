"""
Product model — Inventory items for the Kirana store.
"""

class Product:
    def __init__(self, id=None, name=None, category=None, price=0.0, stock=0, low_stock_threshold=10, unit="pcs", created_at=None, updated_at=None, image_url=None):
        self.id = id
        self.name = name
        self.category = category
        self.price = price
        self.stock = stock
        self.low_stock_threshold = low_stock_threshold
        self.unit = unit
        self.created_at = created_at
        self.updated_at = updated_at
        self.image_url = image_url

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "stock": self.stock,
            "unit": self.unit,
            "low_stock_threshold": self.low_stock_threshold,
            "is_low_stock": self.is_low_stock,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Product {self.name} — stock: {self.stock}>"
