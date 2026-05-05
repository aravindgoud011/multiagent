"""
Inventory — Product CRUD & low-stock alerts.
"""

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.product import Product
from ..utils.helpers import login_required, admin_required

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/products", methods=["POST"])
@admin_required
def add_product():
    data = request.get_json()
    name = data.get("name", "").strip()
    price = data.get("price")

    if not name or price is None:
        return jsonify({"error": "name and price are required"}), 400

    product = Product(
        name=name,
        category=data.get("category", "").strip() or None,
        price=float(price),
        stock=int(data.get("stock", 0)),
        unit=data.get("unit", "pcs").strip(),
        low_stock_threshold=int(data.get("low_stock_threshold", 10)),
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({"message": "Product added", "product": product.to_dict()}), 201


@inventory_bp.route("/products", methods=["GET"])
@login_required
def list_products():
    query = Product.query
    category = request.args.get("category")
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    search = request.args.get("search")
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.order_by(Product.name).all()
    return jsonify({"count": len(products), "products": [p.to_dict() for p in products]}), 200


@inventory_bp.route("/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()
    if "name" in data:
        product.name = data["name"].strip()
    if "category" in data:
        product.category = data["category"].strip() or None
    if "price" in data:
        product.price = float(data["price"])
    if "stock" in data:
        product.stock = int(data["stock"])
    if "unit" in data:
        product.unit = data["unit"].strip()
    if "low_stock_threshold" in data:
        product.low_stock_threshold = int(data["low_stock_threshold"])

    db.session.commit()
    return jsonify({"message": "Product updated", "product": product.to_dict()}), 200


@inventory_bp.route("/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"Product '{product.name}' deleted"}), 200


@inventory_bp.route("/low-stock", methods=["GET"])
@admin_required
def low_stock():
    products = Product.query.filter(
        Product.stock <= Product.low_stock_threshold
    ).order_by(Product.stock.asc()).all()

    return jsonify({
        "count": len(products),
        "products": [p.to_dict() for p in products],
    }), 200
