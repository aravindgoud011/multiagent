from flask import Blueprint, jsonify, request, session
from agents.support_agent import support_agent
from agents.admin_graph import process_admin_query
from ..extensions import get_db_connection
from utils.helpers import admin_required
import datetime

agent_bp = Blueprint("agent", __name__)

@agent_bp.route("/chat", methods=["POST"])
def chat():
    """Endpoint for the customer bot chat."""
    data = request.json
    user_query = data.get("query", "")
    customer_name = session.get("user_name", "Valued Customer")
    
    response = support_agent.process_query(user_query, customer_name)
    return jsonify({"response": response}), 200

@agent_bp.route("/admin/chat", methods=["POST"])
@admin_required
def admin_chat():
    """Endpoint for the admin multi-agent chat."""
    data = request.json
    user_query = data.get("query", "")
    
    try:
        response = process_admin_query(user_query)
        return jsonify({"response": response}), 200
    except Exception as e:
        import traceback
        print(f"Admin Chat Error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to process admin query", "details": str(e)}), 500

@agent_bp.route("/shop-status", methods=["GET"])
def get_status():
    """Get the current shop status."""
    status = support_agent.get_shop_status()
    return jsonify({"status": status}), 200

@agent_bp.route("/toggle-shop", methods=["POST"])
@admin_required
def toggle_shop():
    """Toggle the shop between open and closed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current
    cursor.execute("SELECT [value] FROM settings WHERE [key] = 'shop_status'")
    row = cursor.fetchone()
    current = row[0] if row else "open"
    
    new_status = "closed" if current == "open" else "open"
    
    cursor.execute("UPDATE settings SET [value] = ? WHERE [key] = 'shop_status'", new_status)
    conn.commit()
    conn.close()
    
    return jsonify({"status": new_status, "message": f"Shop is now {new_status}"}), 200

@agent_bp.route("/tickets", methods=["POST"])
def raise_ticket():
    """Create a new support ticket and notify admin."""
    data = request.json
    customer_id = session.get("user_id")
    title = data.get("title")
    description = data.get("description")
    category = data.get("category", "General")

    if not customer_id or not title or not description:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Insert Ticket
    cursor.execute(
        "INSERT INTO support_ticket (customer_id, title, description, category, status, created_at, updated_at) VALUES (?, ?, ?, ?, 'Open', ?, ?)",
        customer_id, title, description, category, datetime.datetime.utcnow(), datetime.datetime.utcnow()
    )
    
    # 2. Notify Admin
    customer_name = session.get("user_name", "A customer")
    notif_title = "New Support Ticket" if category == "General" else "Billing Issue Reported"
    notif_msg = f"{customer_name} raised a {category} ticket: {title}"
    
    # Get admin IDs
    cursor.execute("SELECT id FROM users WHERE role = 'admin'")
    admins = [row[0] for row in cursor.fetchall()]
    
    for admin_id in admins:
        cursor.execute(
            "INSERT INTO notification (title, message, user_id, is_read, created_at) VALUES (?, ?, ?, 0, ?)",
            notif_title, notif_msg, admin_id, datetime.datetime.utcnow()
        )
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Ticket raised successfully"}), 201

@agent_bp.route("/admin/all-tickets", methods=["GET"])
@admin_required
def get_all_tickets():
    """Fetch all support tickets for the admin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Join with users to get customer name
    cursor.execute("""
        SELECT t.id, t.title, t.description, t.category, t.status, t.created_at, u.name as customer_name 
        FROM support_ticket t
        JOIN users u ON t.customer_id = u.id
        ORDER BY t.created_at DESC
    """)
    
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
        
    conn.close()
    return jsonify({"tickets": results}), 200

@agent_bp.route("/admin/resolve-ticket", methods=["POST"])
@admin_required
def resolve_ticket():
    """Resolve a support ticket and notify the customer."""
    data = request.json
    ticket_id = data.get("ticket_id")
    message = data.get("message")
    
    if not ticket_id or not message:
        return jsonify({"error": "Missing ticket ID or message"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Get ticket details to notify the right customer
    cursor.execute("SELECT customer_id, title FROM support_ticket WHERE id = ?", ticket_id)
    ticket = cursor.fetchone()
    
    if not ticket:
        conn.close()
        return jsonify({"error": "Ticket not found"}), 404
        
    # 2. Update status
    cursor.execute(
        "UPDATE support_ticket SET status = 'Closed', updated_at = ? WHERE id = ?",
        datetime.datetime.utcnow(), ticket_id
    )
    
    # 3. Notify Customer
    notif_title = f"Issue Resolved: {ticket.title}"
    notif_msg = f"Your issue has been resolved. Admin message: {message}"
    
    cursor.execute(
        "INSERT INTO notification (title, message, user_id, is_read, created_at) VALUES (?, ?, ?, 0, ?)",
        notif_title, notif_msg, ticket.customer_id, datetime.datetime.utcnow()
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Ticket resolved and customer notified"}), 200
