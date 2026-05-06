"""
Application factory.
"""

import logging
from flask import Flask, jsonify
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Optional: Enable CORS (requires pip install flask-cors)
    try:
        from flask_cors import CORS
        CORS(app)
    except ImportError:
        pass

    # Global JSON Error Handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Always return JSON to prevent frontend parsing errors
        app.logger.error(f"Server Error: {e}")
        # If it's a known HTTP error, extract its code, else default to 500
        code = 500
        if hasattr(e, "code"):
            code = e.code
        return jsonify({"error": "Internal Server Error", "details": str(e)}), code

    # Blueprints
    from .routes.auth import auth_bp
    from .routes.inventory import inventory_bp
    from .routes.billing import billing_bp
    from .routes.payments import payments_bp
    from .routes.customer import customer_bp
    from .routes.pages import pages_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
    app.register_blueprint(billing_bp, url_prefix="/api/billing")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")
    app.register_blueprint(customer_bp, url_prefix="/api/customer")

    return app
