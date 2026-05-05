"""
Application factory.
"""

import logging
from flask import Flask
from .config import Config
from .extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Extensions
    db.init_app(app)

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

    # Create tables
    with app.app_context():
        from . import models
        db.create_all()
        app.logger.info("Database ready.")

    return app
