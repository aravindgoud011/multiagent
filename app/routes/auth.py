"""
Authentication — Register & Login (session-based).
"""

from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    role = data.get("role", "customer").strip().lower()

    if not name or not phone or not password:
        return jsonify({"error": "name, phone, and password are required"}), 400

    if role not in ("admin", "customer"):
        return jsonify({"error": "role must be admin or customer"}), 400

    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "Phone number already registered"}), 409

    status = "approved" if role == "admin" else "pending"
    user = User(name=name, phone=phone, role=role, status=status)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration successful", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")

    if not phone or not password:
        return jsonify({"error": "phone and password are required"}), 400

    user = User.query.filter_by(phone=phone).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid phone or password"}), 401

    if user.status != "approved":
        return jsonify({"error": "Your account is pending admin approval"}), 403

    # Store user info in session
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["role"] = user.role

    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    """Return current logged-in user info."""
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    user = User.query.get(session["user_id"])
    return jsonify({"user": user.to_dict()}), 200
