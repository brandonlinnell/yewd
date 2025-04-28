"""
    Rolsa Technologies
    24/03/2024
    Version v1.0
"""

#   Packages and Libraries
from flask import Flask, render_template, request, redirect, url_for, session
import secrets
import sqlite3
import bcrypt

#   Initialisation
app = Flask(__name__)
app.secret_key = secrets.token_hex(24)


#   Validation and Authentication
def hash_password(password):
    byte_password = password.encode("utf-8")
    hashed = bcrypt.hashpw(byte_password, bcrypt.gensalt())

    return password


def verify_password(stored_password, password_input):
    byte_password = password_input.encode("utf-8")

    return bcrypt.checkpw(byte_password, stored_password)


#   Landing Home Page
@app.route("/")
def home():
    return render_template("home.html")


#   Login Request
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    database = sqlite3.connect("database.db")

    # TODO: Check if chars are in password for security

    # Search database for user information
    query = "SELECT * FROM users WHERE email = ? AND password = ?"
    data = pd.read_sql_query(query, database, params=(email, password))

    # Check for number of available records
    if data.size > 0:
        session["email"] = email
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("home"))


#   Gateway to Login/Register Page
@app.route("/gateway")
def gateway():
    return render_template("login.html")

#   Dashboard Page
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        # Load dashboard stuff

        return render_template("dashboard.html", data=data)
    return render_template("login.html")


#   Products Page
@app.route("/products")
def products():
    return render_template("products.html")


#   Carbon Footprint Page
@app.route("/carbon_footprint")
def carbon_footprint():
    return render_template("carbon_footprint.html")


#   About Page
@app.route("/about")
def about():
    return render_template("about.html")


#   Logout Functionality
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


#   Initalisation
if __name__ == "__main__":
    app.run(debug=True)
