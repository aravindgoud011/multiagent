"""
User model — Admin (shopkeeper) and Customer.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="customer")  # "admin" or "customer"
    status = db.Column(db.String(20), nullable=False, default="pending") # "pending", "approved", "rejected"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---
    bills = db.relationship("Bill", backref="customer", lazy=True)
    payments = db.relationship("Payment", backref="customer", lazy=True)

    # --- Password helpers ---
    def set_password(self, password):
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Return a JSON-safe dictionary (never expose password_hash)."""
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"
