"""
Helper utilities.
"""

from functools import wraps
from flask import session, jsonify


def login_required(fn):
    """Check if user is logged in (session-based)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Please login first"}), 401
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Check if logged-in user is admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Please login first"}), 401
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper
