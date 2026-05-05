"""
Models package — import all models here so that
`from app import models` registers every table with SQLAlchemy.
"""

from .user import User          # noqa: F401
from .product import Product    # noqa: F401
from .bill import Bill, BillItem  # noqa: F401
from .payment import Payment    # noqa: F401
