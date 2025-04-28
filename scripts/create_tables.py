import sqlite3

connection = sqlite3.connect("../database.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    preferred_date DATE NOT NULL,
    postcode TEXT NOT NULL,
    property_type TEXT NOT NULL,
    status TEXT NOT NULL,
    customer_id INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    consultation_id INTEGER NOT NULL,
    maintenance BOOLEAN DEFAULT FALSE,
    date_booked DATE NOT NULL,
    status TEXT NOT NULL
)
""")

connection.commit()
connection.close()
