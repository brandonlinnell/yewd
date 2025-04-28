"""
    Rolsa Technologies
    25/03/2024
    Version v1.1

    Changes - Compared to v1.0:
    + Converted "register" to "signup" for simplicity
    + Added validate password function to check if sign up password
    contains at least one uppercase, lowercase, number, and special character
    + Updated sign up function to check for the requirements and if the password
    is the same as repeat password input for verification
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


def validate_password(password):
    is_uppercase = any(character.isupper() for character in password)
    is_lowercase = any(character.islower() for character in password)
    is_digit = any(character.isdigit() for character in password)
    is_special = any(character in "!@#$%^&*()-_+=<>?/|{}[]" for character in password)

    if is_uppercase and is_lowercase and is_digit and is_special:
        return True  # Password contains one of each requirement
    else:
        return False  # Password does not contain one of each


#   Landing Home Page
@app.route("/")
def home():
    return render_template("home.html")


#   Sign Up Request
@app.route("/signup", methods=["POST"])
def sign_up():
    email = request.form["email"]
    password = request.form["password"]
    repeat_password = request.form["repeat_password"]

    if password != repeat_password:
        return "Passwords do not match"

    if validate_password(password):
        return "Please enter at least one uppercase, lowercase, digit and special character"

    return "Sign up successful"


#   Login Request
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    database = sqlite3.connect("database.db")

    # Search database for user information
    query = "SELECT * FROM users WHERE email = ? AND password = ?"
    data = pd.read_sql_query(query, database, params=(email, password))

    # Check for number of available records
    if data.size > 0:
        session["email"] = email
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("home"))


#   Gateway to Login Page
@app.route("/login_page")
def login_page():
    return render_template("login.html")


#   Gateway to Sign Up Page
@app.route("/signup_page")
def signup_page():
    return render_template("signup.html")


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
