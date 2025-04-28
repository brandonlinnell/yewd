"""
    Rolsa Technologies
    31/03/2024
    Version v3.2 - Login Page Testing

    Changes - Compared to v3.1:
    + Modified sanitisation functionality
    + Added check in /login route to return error message if email contains invalid characters
    + Conducted thorough testing of login functionality
"""

#   Packages and Libraries
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
from flask_session import Session
from dotenv import load_dotenv
import html
import sqlite3
import bcrypt
import os


#   Initialisation
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_USE_SIGNER"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_FILE_DIR"] = "./.sessions"

Session(app)

@app.context_processor  # Integrating account status across all templates
def logged_in():
    return dict(logged_in="user" in session)


#   Validation, Security and Authentication
def sanitise_input(string):
    # Sanitsation method for SQL injection and XSS prevention
    if input is None:
        return ""

    input_string = str(string).strip()
    if any(char in input_string for char in ["'", ";", "--"]):
        return None

    return html.escape(input_string)


def hash_password(password):  # SHA-256 bcrypt encryption
    byte_password = password.encode("utf-8")
    hashed = bcrypt.hashpw(byte_password, bcrypt.gensalt())

    return hashed  # Returns the hashed password


def verify_password(stored_password, password_input):
    byte_password = password_input.encode("utf-8")
    byte_stored_password = stored_password.encode("utf-8")

    return bcrypt.checkpw(byte_password, byte_stored_password)  # Returns boolean depending on if password is correct


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
    email = sanitise_input(request.form["email"])
    password = request.form["password"]
    repeat_password = request.form["repeat_password"]

    if email is None:
        return render_template("signup.html", error="Invalid characters in email")

    if password != repeat_password:  # Checks if password fields are not the same
        return render_template("signup.html", error="Passwords don't match")

    if not validate_password(password):  # Checks for appropriate validation of password
        return render_template("signup.html",
                               error="Please enter at least one uppercase, lowercase, digit, and special character")

    try:
        database = sqlite3.connect("../database.db")
        cursor = database.cursor()

        # Creates database entry in customers database
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT DEFAULT "",
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
        """, ("", email, hashed_password.decode("utf-8"), created_time))

        database.commit()
    except sqlite3.IntegrityError:  # Checking for email already registered
        return render_template("signup.html", error="Email already registered")
    except Exception as error:  # Checking for any server-sided errors
        return render_template("signup.html", error=f"An error occurred: {error}")
    finally:  # Successful
        database.close()

    # Sends user straight to login page
    return render_template("login.html", success="Success. Please log in to your account")


#   Login Request
@app.route("/login", methods=["POST"])
def login():
    email = sanitise_input(request.form["email"])
    password = request.form["password"]
    stay_logged_in = request.form.get("stay_logged_in")
    next_url = request.form.get("next")  # Get the next URL from the form

    if email is None:
        return render_template("login.html", error="Invalid characters in email")

    try:
        database = sqlite3.connect("../database.db")
        cursor = database.cursor()

        cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:  # Check if user exists in the database
            if verify_password(user[3], password):  # user[3] is the stored hashed password
                session["user"] = email

                if stay_logged_in:
                    session.permanent = True  # Permanent session

                # Redirect to next_url if provided, otherwise to dashboard
                if next_url:
                    return redirect(next_url)

                return redirect(url_for("dashboard"))
            else:
                # Incorrect password
                return render_template("login.html", error="Incorrect password", next=next_url)
        else:  # Account does not exist
            return render_template("login.html", error="Account does not exist with this email", next=next_url)
    except Exception as error:  # Any other errors on server
        return render_template("login.html", error=f"An error occurred: {error}", next=next_url)
    finally:
        database.close()


#   Gateway to Login Page
@app.route("/login-page")
def login_page():
    return render_template("login.html")


#   Gateway to Sign Up Page
@app.route("/signup-page")
def signup_page():
    return render_template("signup.html")


#   Schedule Consultation Page
@app.route("/schedule-page")
def schedule_page():
    if "user" in session:
        return render_template("consultation.html")

    return render_template("login.html", error="You must be logged in to continue", next=request.url)


#   Submit Consultation Request
@app.route("/submit-consultation", methods=["POST"])
def submit_consultation():
    data = request.get_json()  # Get JSON data from the request

    product_id = data.get("product_id")
    full_name = sanitise_input(data.get("full_name"))
    preferred_date = sanitise_input(data.get("preferred_date"))
    postcode = sanitise_input(data.get("postcode"))
    property_type = data.get("property_type")
    customer_email = session.get("user")

    if not customer_email:  # Make sure user is logged in
        return jsonify({"success": False, "error": "You must log in to continue"})
    try:
        database = sqlite3.connect("../database.db")
        cursor = database.cursor()

        # Fetch customer_id from user session
        cursor.execute("SELECT id FROM customers WHERE email = ?", (customer_email,))
        customer = cursor.fetchone()

        # Server-side validation
        if not product_id or not full_name or not preferred_date or not postcode or not property_type:
            return jsonify({"success": False, "error": "Fields cannot be empty"})

        if not customer:
            return jsonify({"success": False, "error": "User not in session"})

        # Ensure full_name contains only letters/spaces
        if not all(char.isalpha() or char.isspace() for char in full_name):
            return jsonify({"success": False, "error": "Full name must contain only letters and spaces, no numbers"})

        # Ensure full_name is not just empty white spaces
        if not full_name.strip() or not any(char.isalpha() for char in full_name):
            return jsonify({"success": False, "error": "Full name must contain at least one letter, not just spaces"})

        # Ensure postcode is 8 characters or fewer
        if len(postcode) > 8:
            return jsonify({"success": False, "error": "Postcode must be 8 characters or less"})

        # Ensure preferred date is after today
        today = datetime.now().date()
        date_data = datetime.strptime(preferred_date, "%Y-%m-%d").date()

        if date_data <= today:
            return jsonify({"success": False, "error": "Preferred date must be after today"})

        customer_id = customer[0]

        # Update full_name in the customers table
        cursor.execute("""
        UPDATE customers
        SET full_name = ?
        WHERE id = ?
        """, (full_name, customer_id))

        # Insert consultation details into database
        cursor.execute("""
        INSERT INTO consultations (product_id, preferred_date, postcode, property_type, status, customer_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id, preferred_date, postcode, property_type, "pending", customer_id))

        database.commit()
        return jsonify({"success": True})
    except Exception as error:
        return jsonify({"success": False, "error": f"An error occurred: {error}"})
    finally:
        database.close()


#   Dashboard Page
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        # Load dashboard stuff

        return render_template("dashboard.html")
    return render_template("login.html", error="You must be logged in to continue")


#   Products API
@app.route("/api/products", methods=["GET"])
def get_products():
    database = sqlite3.connect("../database.db")
    cursor = database.cursor()

    # Updated query to include the new details column
    cursor.execute("SELECT type, description, image, details FROM products")
    products_table = cursor.fetchall()

    product_data = {}
    for product in products_table:
        product_type, description, image, details = product
        product_data[product_type] = {
            "extra": description,
            "image": image,
            "details": details
        }

    database.close()

    return jsonify(product_data)


#   Products Page
@app.route("/products")
def products():
    return render_template("products.html")


#   Carbon Footprint
carbon_data = {
    "individual": {
        "transport_miles": 0.171,  # kg CO2e per mile (UK avg car, 2023)
        "electricity_kwh": 0.212,  # kg CO2e per kWh (UK grid avg, 2023)
        "meat_meals": 2.0,  # kg CO2e per meat meal (UK avg)
    },
    "commercial": {
        "electricity_kwh": 0.212,  # kg CO2e per kWh (UK grid avg)
        "gas_kwh": 0.182,  # kg CO2e per kWh (UK gas)
        "waste_tonnes": 0.403  # kg CO2e per kg of waste (UK avg, scaled to tonnes)
    }
}


#   Carbon Footprint Page
@app.route("/carbonfootprint")
def carbon_footprint():
    return render_template("carbonfootprint.html")


@app.route("/get-carbon", methods=["POST"])
def calculate_carbon():
    data = request.json
    user_type = data.get("type")  # "individual" or "commercial"

    try:
        if user_type == "individual":
            miles = float(data.get("transport_miles") or 0)  # Annual miles
            kWh = float(data.get("electricity_kwh") or 0)  # Monthly kWh
            meals = float(data.get("meat_meals") or 0)  # Weekly meals

            # Validation ensures no negative values
            if miles < 0 or kWh < 0 or meals < 0:
                return jsonify({"error": "Values cannot be negative"}), 400

            # Convert inputs into yearly
            annual_kWh = kWh * 12  # Convert monthly to annual
            annual_meals = meals * 52  # Convert weekly to annual

            footprint = (miles * carbon_data["individual"]["transport_miles"] +
                         annual_kWh * carbon_data["individual"]["electricity_kwh"] +
                         annual_meals * carbon_data["individual"]["meat_meals"]) / 1000
            average = 4.6  # UK avg individual footprint in tonnes CO2e (2023 estimate)

        else:  # Commercial
            kWh = float(data.get("electricity_kwh") or 0)  # Monthly kWh
            gas_kWh = float(data.get("gas_kwh") or 0)  # Monthly kWh
            waste_tonnes = float(data.get("waste_tonnes") or 0)  # Annual tonnes

            # Validation ensures no negative values
            if kWh < 0 or gas_kWh < 0 or waste_tonnes < 0:
                return jsonify({"error": "Values cannot be negative"}), 400

            # Convert inputs into yearly
            annual_kWh = kWh * 12
            annual_gas_kWh = gas_kWh * 12

            footprint = (annual_kWh * carbon_data["commercial"]["electricity_kwh"] +
                         annual_gas_kWh * carbon_data["commercial"]["gas_kwh"] +
                         waste_tonnes * carbon_data["commercial"]["waste_tonnes"]) / 1000
            average = 15.0  # UK avg household/commercial footprint in tonnes CO2e

        return jsonify({
            "footprint": round(footprint, 2),
            "average": average
        })

    except ValueError:
        return jsonify({"error": "Invalid input - please enter numeric values"}), 400


#   About Page
@app.route("/about")
def about():
    return render_template("about.html")


#   Logout Functionality
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


#   Initialisation
if __name__ == "__main__":
    app.run(debug=True)