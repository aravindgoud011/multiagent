"""
User model — Admin (shopkeeper) and Customer.
"""

from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, id=None, name=None, phone=None, password_hash=None, role="customer", status="pending", created_at=None):
        self.id = id
        self.name = name.strip() if name else None
        self.phone = phone.strip() if phone else None
        self.password_hash = password_hash
        self.role = role.strip().lower() if role else "customer"
        self.status = status.strip().lower() if status else "pending"
        self.created_at = created_at

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"
