"""
Authentication — Register & Login (session-based).
"""

from flask import Blueprint, request, jsonify, session
from ..extensions import get_db_connection
from ..models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400
            
        name = data.get("name", "").strip()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        role = data.get("role", "customer").strip().lower()

        if not name or not phone or not password:
            return jsonify({"error": "name, phone, and password are required"}), 400

        if role not in ("admin", "customer"):
            return jsonify({"error": "role must be admin or customer"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE phone = ?", phone)
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Phone number already registered"}), 409

        status = "approved" if role == "admin" else "pending"
        user = User(name=name, phone=phone, role=role, status=status)
        user.set_password(password)
        
        cursor.execute(
            "INSERT INTO users (name, phone, password_hash, role, status) VALUES (?, ?, ?, ?, ?)",
            (user.name, user.phone, user.password_hash, user.role, user.status)
        )
        
        # Create Notification for admin if it's a customer
        if role == 'customer':
            cursor.execute(
                "INSERT INTO notification (title, message) VALUES (?, ?)",
                ("New Registration", f"Customer {name} ({phone}) has registered and is pending approval.")
            )
            
        conn.commit()
        
        cursor.execute("SELECT id, created_at FROM users WHERE phone = ?", phone)
        row = cursor.fetchone()
        user.id = row.id
        user.created_at = row.created_at
        conn.close()

        return jsonify({"message": "Registration successful", "user": user.to_dict()}), 201

    except Exception as e:
        import traceback
        print("ERROR IN /register:", traceback.format_exc())
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")

    if not phone or not password:
        return jsonify({"error": "phone and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, password_hash, role, status, created_at FROM users WHERE phone = ?", phone)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Invalid phone or password"}), 401

    user = User(id=row.id, name=row.name, phone=row.phone, password_hash=row.password_hash, role=row.role, status=row.status, created_at=row.created_at)

    if not user.check_password(password):
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
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, role, status, created_at FROM users WHERE id = ?", session["user_id"])
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "User not found"}), 404
        
    user = User(id=row.id, name=row.name, phone=row.phone, role=row.role, status=row.status, created_at=row.created_at)
    return jsonify({"user": user.to_dict()}), 200
@auth_bp.route("/approve/<int:user_id>", methods=["POST"])
def approve_user(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = 'approved' WHERE id = ?", user_id)
    conn.commit()
    conn.close()
    return jsonify({"message": "User approved successfully"}), 200
