"""
    Rolsa Technologies
    25/03/2024
    Version v1.2

    Changes - Compared to v1.1:
    + Implemented datetime module/library for fetching time & date
    + Updated encryption and password verification
    + Created database connection and execution when signing up
    + Checked to see if account exists when logging in
    + Added additional checks across server when signing up/signing in
    + Added comments to show processes and break it down for future use by third parties
"""

#   Packages and Libraries
from flask import Flask, render_template, request, redirect, url_for, session
import secrets
from datetime import datetime
import sqlite3
import bcrypt

#   Initialisation
app = Flask(__name__)
app.secret_key = secrets.token_hex(24)


#   Validation and Authentication
def hash_password(password): # SHA-256 bcrypt encryption
    byte_password = password.encode("utf-8")
    hashed = bcrypt.hashpw(byte_password, bcrypt.gensalt())

    return hashed # Returns the hashed password


def verify_password(stored_password, password_input):
    byte_password = password_input.encode("utf-8")
    byte_stored_password = stored_password.encode("utf-8")

    return bcrypt.checkpw(byte_password, byte_stored_password) # Returns boolean depending on if password is correct

def validate_password(password):
    is_uppercase = any(character.isupper() for character in password)
    is_lowercase = any(character.islower() for character in password)
    is_digit = any(character.isdigit() for character in password)
    is_special = any(character in "!@#$%^&*()-_+=<>?/|{}[]" for character in password)

    if is_uppercase and is_lowercase and is_digit and is_special:
        return True # Password contains one of each requirement
    else:
        return False # Password does not contain one of each

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

    if password != repeat_password: # Checks if password fields are not the same
        return render_template("signup.html", error="Passwords don't match")

    if not validate_password(password): # Checks for appropriate validation of password
        return render_template("signup.html",
                               error="Please enter at least one uppercase, lowercase, digit, and special character")

    try:
        database = sqlite3.connect("database.db")
        cursor = database.cursor()

        # Creates database entry in customers database
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT DEFAULT '',
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_time TEXT NOT NULL
        )
        """)

        # Checks if the email is already registered
        cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
        if cursor.fetchone():
            return render_template("signup.html", error="Email already registered")

        hashed_password = hash_password(password)
        created_time = datetime.now().strftime("%Y-%d-%m %H:%M:%S")

        # Executes and inserts customer data into customers table
        cursor.execute("""
        INSERT INTO customers (full_name, email, password, created_time)
        VALUES (?, ?, ?, ?)
        """, ('', email, hashed_password.decode('utf-8'), created_time))

        database.commit()
    except sqlite3.IntegrityError: # Checking for email already registered
        return render_template("signup.html", error="Email already registered")
    except Exception as error: # Checking for any server-sided errors
        return render_template("signup.html", error=f"An error occurred: {error}")
    finally: # Successful
        database.close()

    # Sends user straight to login page
    return render_template("login.html", success="Success. Please log in to your account")


#   Login Request
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    try:
        database = sqlite3.connect("database.db")
        cursor = database.cursor()

        cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user: # Check if user exists in the database
            if verify_password(user[3], password):  # user[3] is the stored hashed password
                session["user"] = email
                # Successful log in
                return render_template("login.html", success="Logged in successfully")
            else:
                # Incorrect password
                return render_template("login.html", error="Incorrect password")
        else: # Account does not exist
            return render_template("login.html", error="Account does not exist with this email")
    except Exception as error: # Any other errors on server
        return render_template("login.html", error=f"An error occurred: {error}")
    finally:
        database.close()

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