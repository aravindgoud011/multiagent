from flask import Blueprint, jsonify, request
from ..extensions import get_db_connection
from ..models.notification import Notification
from ..utils.helpers import admin_required

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/all", methods=["GET"])
@admin_required
def get_notifications():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notification ORDER BY created_at DESC")
    
    notifications = []
    for row in cursor.fetchall():
        n = Notification(
            id=row.id,
            title=row.title,
            message=row.message,
            is_read=bool(row.is_read),
            created_at=row.created_at
        )
        notifications.append(n.to_dict())
    
    conn.close()
    return jsonify({"notifications": notifications}), 200

@notifications_bp.route("/mark-read/<int:notif_id>", methods=["POST"])
@admin_required
def mark_read(notif_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notification SET is_read = 1 WHERE id = ?", notif_id)
    conn.commit()
    conn.close()
    return jsonify({"message": "Notification marked as read"}), 200

@notifications_bp.route("/mark-all-read", methods=["POST"])
@admin_required
def mark_all_read():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notification SET is_read = 1")
    conn.commit()
    conn.close()
    return jsonify({"message": "All notifications marked as read"}), 200

@notifications_bp.route("/unread-count", methods=["GET"])
@admin_required
def unread_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notification WHERE is_read = 0 AND user_id IS NULL")
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({"unread_count": count}), 200

# --- Customer Notification Routes ---

@notifications_bp.route("/customer/all", methods=["GET"])
def get_customer_notifications():
    from flask import session
    if "user_id" not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session["user_id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notification WHERE user_id = ? ORDER BY created_at DESC", user_id)
    
    notifications = []
    for row in cursor.fetchall():
        notifications.append({
            "id": row.id,
            "title": row.title,
            "message": row.message,
            "is_read": bool(row.is_read),
            "created_at": row.created_at.isoformat()
        })
    
    conn.close()
    return jsonify({"notifications": notifications}), 200

@notifications_bp.route("/customer/unread-count", methods=["GET"])
def get_customer_unread_count():
    from flask import session
    if "user_id" not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session["user_id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notification WHERE user_id = ? AND is_read = 0", user_id)
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({"unread_count": count}), 200

@notifications_bp.route("/customer/mark-all-read", methods=["POST"])
def customer_mark_all_read():
    from flask import session
    if "user_id" not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session["user_id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notification SET is_read = 1 WHERE user_id = ?", user_id)
    conn.commit()
    conn.close()
    return jsonify({"message": "All notifications marked as read"}), 200
