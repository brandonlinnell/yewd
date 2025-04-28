"""
    Rolsa Technologies
    01/04/2024
    Version v4.1 - Energy usage tracking

    Changes - Compared to v4.0:
    + Added energy tracking usage API endpoint
        + Generates a week of example energy usage data
        + Provides a UK average of 7.4 kWh per day
        + Returns JSON data to client to present graph data and statistics
"""

#   Packages and Libraries
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
from flask_session import Session
from dotenv import load_dotenv
import random
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
    if string is None:
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

    # Checks if password fields are not the same
    if password != repeat_password:
        return render_template("signup.html", error="Passwords don't match")

    # Checks for appropriate validation of password
    if not validate_password(password):
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
    except sqlite3.IntegrityError:
        # Checking for email already registered
        return render_template("signup.html", error="Email already registered")
    except Exception as error:
        # Checking for any server-sided errors
        return render_template("signup.html", error=f"An error occurred: {error}")
    finally:
        # Successful
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
        else:
            # Account does not exist
            return render_template("login.html", error="Account does not exist with this email", next=next_url)
    except Exception as error:
        # Any other errors on server
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

    product_type = data.get("product_type")
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
        if not product_type or not full_name or not preferred_date or not postcode or not property_type:
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

        # Fetch product id from products table based on product type (str)
        cursor.execute("SELECT id FROM products WHERE type = ?", (product_type,))
        product = cursor.fetchone()

        if not product:
            return jsonify({"success": False, "error": "Product not found"})

        product_id = product[0]
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
        """, (product_id, preferred_date, postcode, property_type, "approved", customer_id))

        database.commit()
        # Return JSON with redirect URL instead of redirect
        return jsonify({"success": True, "redirect": url_for("dashboard")})
    except Exception as error:
        return jsonify({"success": False, "error": f"An error occurred: {error}"})
    finally:
        database.close()


#   Cancel Consultation
@app.route("/cancel-consultation", methods=["POST"])
def cancel_consultation():
    if "user" not in session:
        return jsonify({"success": False, "error": "You must be logged in to continue"})

    # Check if consultation_id exists
    consultation_id = request.form.get("consultation_id")
    if not consultation_id:
        return jsonify({"success": False, "error": "Consultation id required"})
    try:
        database = sqlite3.connect("../database.db")
        cursor = database.cursor()

        # Delete related bookings first
        cursor.execute(
            "DELETE FROM bookings WHERE consultation_id = ? AND customer_id = (SELECT id FROM customers WHERE email = ?)",
            (consultation_id, session["user"]))

        # Then delete the consultation
        cursor.execute(
            "DELETE FROM consultations WHERE id = ? AND customer_id = (SELECT id FROM customers WHERE email = ?)",
            (consultation_id, session["user"]))
        database.commit()
        return jsonify({"success": "Consultation successfully cancelled"})
    except Exception as error:
        return jsonify({"success": False, "error": f"An error occurred: {error}"})
    finally:
        database.close()


#   Scheduling for Installation/Maintenance
@app.route("/schedule-request", methods=["POST"])
def schedule_request():
    if "user" not in session:
        return render_template("login.html", error="You must be logged in to continue", next=url_for("dashboard")), 401

    consultation_id = request.form.get("consultation_id")
    schedule_date = request.form.get("schedule_date")
    service_type = request.form.get("service_type")  # "installation" or "maintenance"

    # Validation
    if not consultation_id or not schedule_date or not service_type:
        return jsonify(
            {"success": False, "error": "Consultation ID, schedule date, and service type are required"}), 400

    # Ensure consultation_id is an integer
    try:
        consultation_id = int(consultation_id)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid consultation ID"}), 400

    # Validate date format
    try:
        datetime.strptime(schedule_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        database = sqlite3.connect("../database.db")
        cursor = database.cursor()

        # Verify the consultation exists
        cursor.execute("""
            SELECT status FROM consultations
            WHERE id = ? AND customer_id = (SELECT id FROM customers WHERE email = ?)
        """, (consultation_id, session["user"]))
        consultation = cursor.fetchone()

        if not consultation:
            return jsonify({"success": False, "error": "Consultation not found or does not belong to you"}), 404

        # Check if installation requires approved status
        if service_type == "installation" and consultation[0] != "approved":
            return jsonify({"success": False, "error": "Consultation must be approved to schedule installation"}), 400

        # Validate schedule date
        today = datetime.now().date()
        date_data = datetime.strptime(schedule_date, "%Y-%m-%d").date()
        if date_data <= today:
            return jsonify({"success": False, "error": "Schedule date must be after today"}), 400

        # Get customer id
        cursor.execute("SELECT id FROM customers WHERE email = ?", (session["user"],))
        customer_id = cursor.fetchone()[0]

        # Determine maintenance flag and status
        is_maintenance = service_type == "maintenance"
        status = "Maintenance Scheduled" if is_maintenance else "Installation Scheduled"

        # Insert into bookings table
        cursor.execute("""
            INSERT INTO bookings (customer_id, consultation_id, maintenance, date_booked, status)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, consultation_id, is_maintenance, schedule_date, "Scheduled"))

        # Update the consultation status and date
        cursor.execute("""
            UPDATE consultations
            SET status = ?, preferred_date = ?
            WHERE id = ?
        """, (status, schedule_date, consultation_id))

        database.commit()
        return jsonify({"success": True, "message": f"{service_type.capitalize()} successfully scheduled"})
    except Exception as error:
        return jsonify({"success": False, "error": f"An error occurred: {error}"}), 500
    finally:
        database.close()


#   Consultations API
@app.route("/api/consultations", methods=["GET"])
def get_consultations():
    if "user" not in session:
        return render_template("login.html", error="You must be logged in to continue")
    try:
        database = sqlite3.connect("../database.db")
        cursor = database.cursor()

        # Fetch customer id
        cursor.execute("SELECT id FROM customers WHERE email = ?", (session["user"],))
        customer = cursor.fetchone()

        if not customer:
            return jsonify({"success": False, "error": "Customer not found"})

        customer_id = customer[0]

        cursor.execute("""
            SELECT c.id, p.type, c.preferred_date, c.status
            FROM consultations c
            JOIN products p ON c.product_id = p.id
            WHERE c.customer_id = ?
            ORDER BY c.preferred_date DESC
        """, (customer_id,))
        consultations = cursor.fetchall()

        consultation_data = []
        for row in consultations:
            consultation = {
                "id": row[0],
                "product_type": row[1],
                "date_scheduled": row[2],
                "status": row[3],
            }

            consultation_data.append(consultation)

        return jsonify({"success": True, "consultations": consultation_data})
    except Exception as error:
        return jsonify({"success": False, "error": f"An error occurred: {error}"})
    finally:
        database.close()


#   Dashboard Page
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        print("No user in session, redirecting to login")
        return render_template("login.html", error="You must be logged in to continue", next=request.url)

    try:
        database = sqlite3.connect("../database.db")
        cursor = database.cursor()

        # Fetch customer_id and full_name
        cursor.execute("SELECT id, full_name FROM customers WHERE email = ?", (session["user"],))
        customer = cursor.fetchone()

        if not customer:
            return render_template("dashboard.html", error="User not found", consultations=[])

        customer_id, full_name = customer
        user_name = full_name.strip() if full_name and full_name.strip() else "user"

        # Fetch all consultations with product type
        cursor.execute("""
            SELECT p.type, c.preferred_date, c.property_type, c.status, c.id
            FROM consultations c
            JOIN products p ON c.product_id = p.id
            WHERE c.customer_id = ?
            ORDER BY c.preferred_date ASC
        """, (customer_id,))
        consultations = cursor.fetchall()

        # Prepare consultation data
        consultation_data = []
        today = datetime.now().date()
        next_consultation = None
        latest_consultation = None

        for row in consultations:
            product_type, preferred_date, property_type, status, consultation_id = row
            date_obj = datetime.strptime(preferred_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d/%m/%Y")

            # Determine request_type based on status
            request_type = "Enquiry"
            if status == "Installation Scheduled":
                request_type = "Installation"
            elif status == "Maintenance Scheduled":
                request_type = "Maintenance"

            consultation = {
                "product_id": product_type,
                "request_type": request_type,
                "property_type": property_type,
                "date_scheduled": formatted_date,
                "status": status,
                "consultation_id": consultation_id,
                "date_obj": date_obj
            }
            consultation_data.append(consultation)

            # Next closest
            if date_obj.date() > today and next_consultation is None:
                next_consultation = consultation

            # Latest updated
            if latest_consultation is None or date_obj > latest_consultation["date_obj"]:
                latest_consultation = consultation

        return render_template(
            "dashboard.html",
            consultations=consultation_data,
            user_name=user_name,
            next_consultation=next_consultation,
            latest_consultation=latest_consultation
        )
    except Exception as error:
        print(f"Exception occurred: {error}")
        return render_template("dashboard.html", error=f"An error occurred: {error}", consultations=[])
    finally:
        database.close()


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


#   Energy Usage
@app.route("/api/energy-usage", methods=["GET"])
def track_energy_usage():
    # Generate current week data
    today = datetime.now().date()
    dates = []
    for x in range(6, -1, -1): dates.append(today - timedelta(days=x))

    # Generate random energy usage values (kWh)
    user_values = []
    for _ in range(7): user_values.append(random.randint(3, 7))

    national_average = [7.4] * 7  # 2700 kWh per year

    graph_stuff = {
        "labels": [date.strftime("%d/%m") for date in dates],
        "user_values": user_values,
        "national_average": national_average
    }

    # Calculate statistics and return result
    daily_usage = user_values[-1]
    weekly_usage = sum(user_values)
    monthly_usage = weekly_usage * 4
    avg_daily_usage = round(weekly_usage / len(user_values), 1)

    return jsonify({
        "success": True,
        "graph_data": graph_stuff,
        "daily_usage": daily_usage,
        "weekly_usage": weekly_usage,
        "monthly_usage": round(monthly_usage),
        "avg_daily_usage": avg_daily_usage
    })


#   Products Page
@app.route("/products")
def products():
    return render_template("products.html")


#   Carbon Footprint
carbon_data = {
    "individual": {
        "transport_miles": 0.18294,  # kg CO₂e per mile (average UK car, 2023)
        "electricity_kwh": 0.19338,  # kg CO₂e per kWh (UK grid average, 2023)
        "meat_meals": 2.0,  # kg CO₂e per meat meal (general estimate)
    },
    "commercial": {
        "electricity_kwh": 0.19338,  # kg CO₂e per kWh (UK grid average, 2023)
        "gas_kwh": 0.18316,  # kg CO₂e per kWh (natural gas, 2023)
        "waste_tonnes": 403.0  # kg CO₂e per tonne of waste (general estimate)
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
