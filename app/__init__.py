"""
Application factory.
"""

import os
import logging
import sys
from flask import Flask, jsonify

# Add root and utils to path for standalone script imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .backend.config import Config

def create_app():
    # Configure Flask to use the new frontend directory
    app = Flask(__name__, 
                template_folder='frontend/templates',
                static_folder='frontend/static')
    
    app.config.from_object(Config)

    # Initialize Database Schema & Seed (Import from utils)
    from utils.create_tables import create_azure_sql_tables
    from utils.seed import seed_database
    try:
        create_azure_sql_tables()
        seed_database()
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")

    # Logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Optional: Enable CORS
    try:
        from flask_cors import CORS
        CORS(app)
    except ImportError:
        pass

    # Global JSON Error Handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Server Error: {e}")
        code = 500
        if hasattr(e, "code"):
            code = e.code
        return jsonify({"error": "Internal Server Error", "details": str(e)}), code

    # Blueprints (Imported from backend.routes)
    from .backend.routes.auth import auth_bp
    from .backend.routes.inventory import inventory_bp
    from .backend.routes.billing import billing_bp
    from .backend.routes.payments import payments_bp
    from .backend.routes.customer import customer_bp
    from .backend.routes.pages import pages_bp
    from .backend.routes.notifications import notifications_bp
    from .backend.routes.ml_routes import ml_bp
    from .backend.routes.agent_routes import agent_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(ml_bp, url_prefix="/api/ml")
    app.register_blueprint(agent_bp, url_prefix="/api/agent")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
    app.register_blueprint(billing_bp, url_prefix="/api/billing")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")
    app.register_blueprint(customer_bp, url_prefix="/api/customer")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    return app
