"""
Pages blueprint — serves HTML pages.
"""

from flask import Blueprint, render_template, session, redirect, url_for

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    if "user_id" in session:
        if session["role"] == "admin":
            return redirect(url_for("pages.admin_dashboard"))
        return redirect(url_for("pages.customer_dashboard"))
    return redirect(url_for("pages.login_page"))


@pages_bp.route("/login")
def login_page():
    return render_template("login.html")


@pages_bp.route("/register")
def register_page():
    return render_template("register.html")


@pages_bp.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("pages.login_page"))
    return render_template("admin_dashboard.html")


@pages_bp.route("/customer/dashboard")
def customer_dashboard():
    if "user_id" not in session:
        return redirect(url_for("pages.login_page"))
    return render_template("customer_dashboard.html")
