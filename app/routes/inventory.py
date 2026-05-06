"""
Inventory — Product CRUD & low-stock alerts.
"""

import os
from flask import Blueprint, request, jsonify, url_for
from werkzeug.utils import secure_filename
from ..extensions import get_db_connection
from ..models.product import Product
from ..utils.helpers import login_required, admin_required

inventory_bp = Blueprint("inventory", __name__)

@inventory_bp.route("/upload_image", methods=["POST"])
@admin_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    filename = secure_filename(file.filename)
    # Ensure static/uploads exists
    upload_folder = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    image_url = url_for('static', filename=f'uploads/{filename}')
    return jsonify({"image_url": image_url}), 200


@inventory_bp.route("/products", methods=["POST"])
@admin_required
def add_product():
    data = request.get_json()
    name = data.get("name", "").strip()
    price = data.get("price")

    if not name or price is None:
        return jsonify({"error": "name and price are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    product = Product(
        name=name,
        category=data.get("category", "").strip() or None,
        price=float(price),
        stock=int(data.get("stock", 0)),
        unit=data.get("unit", "pcs").strip(),
        low_stock_threshold=int(data.get("low_stock_threshold", 10)),
        image_url=data.get("image_url", "").strip() or None
    )
    
    cursor.execute(
        "INSERT INTO product (name, category, price, stock, low_stock_threshold, unit, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (product.name, product.category, product.price, product.stock, product.low_stock_threshold, product.unit, product.image_url)
    )
    conn.commit()
    
    cursor.execute("SELECT @@IDENTITY AS id")
    product.id = cursor.fetchone()[0]
    conn.close()

    return jsonify({"message": "Product added", "product": product.to_dict()}), 201


@inventory_bp.route("/products", methods=["GET"])
@login_required
def list_products():
    category = request.args.get("category")
    search = request.args.get("search")
    
    query = "SELECT id, name, category, price, stock, low_stock_threshold, unit, image_url, created_at, updated_at FROM product WHERE 1=1"
    params = []
    
    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")
    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")
        
    query += " ORDER BY name"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    products = []
    for row in cursor.fetchall():
        p = Product(id=row.id, name=row.name, category=row.category, price=row.price, stock=row.stock, 
                    low_stock_threshold=row.low_stock_threshold, unit=row.unit, image_url=row.image_url, created_at=row.created_at, updated_at=row.updated_at)
        products.append(p)
        
    conn.close()

    return jsonify({"count": len(products), "products": [p.to_dict() for p in products]}), 200


@inventory_bp.route("/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM product WHERE id = ?", product_id)
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()
    updates = []
    params = []
    
    if "name" in data:
        updates.append("name = ?")
        params.append(data["name"].strip())
    if "category" in data:
        updates.append("category = ?")
        params.append(data["category"].strip() or None)
    if "price" in data:
        updates.append("price = ?")
        params.append(float(data["price"]))
    if "stock" in data:
        updates.append("stock = ?")
        params.append(int(data["stock"]))
    if "unit" in data:
        updates.append("unit = ?")
        params.append(data["unit"].strip())
    if "low_stock_threshold" in data:
        updates.append("low_stock_threshold = ?")
        params.append(int(data["low_stock_threshold"]))
    if "image_url" in data:
        updates.append("image_url = ?")
        params.append(data["image_url"].strip() or None)
        
    if updates:
        updates.append("updated_at = GETUTCDATE()")
        query = f"UPDATE product SET {', '.join(updates)} WHERE id = ?"
        params.append(product_id)
        cursor.execute(query, params)
        conn.commit()
        
    cursor.execute("SELECT id, name, category, price, stock, low_stock_threshold, unit, image_url, created_at, updated_at FROM product WHERE id = ?", product_id)
    row = cursor.fetchone()
    conn.close()
    
    product = Product(id=row.id, name=row.name, category=row.category, price=row.price, stock=row.stock, 
                    low_stock_threshold=row.low_stock_threshold, unit=row.unit, image_url=row.image_url, created_at=row.created_at, updated_at=row.updated_at)

    return jsonify({"message": "Product updated", "product": product.to_dict()}), 200


@inventory_bp.route("/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM product WHERE id = ?", product_id)
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    cursor.execute("DELETE FROM product WHERE id = ?", product_id)
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"Product '{row.name}' deleted"}), 200


@inventory_bp.route("/low-stock", methods=["GET"])
@admin_required
def low_stock():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM product WHERE stock <= low_stock_threshold ORDER BY stock ASC")
    
    products = []
    for row in cursor.fetchall():
        p = Product(id=row.id, name=row.name, category=row.category, price=row.price, stock=row.stock, 
                    low_stock_threshold=row.low_stock_threshold, unit=row.unit, created_at=row.created_at, updated_at=row.updated_at)
        products.append(p)
        
    conn.close()

    return jsonify({
        "count": len(products),
        "products": [p.to_dict() for p in products],
    }), 200
