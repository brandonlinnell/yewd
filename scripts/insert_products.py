import sqlite3

connection = sqlite3.connect("../database.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    details TEXT NOT NULL,
    image TEXT NOT NULL
)
""")

products_data = [
    ("Solar panels", "Cut your costs with our energy efficient solar panels", "Our solar panels utilise cutting-edge technology to provide efficient, renewable energy "
                     "solutions.", "/static/assets/product_icons/solarpanels.png"),
    ("EV charging stations", "Go more hybrid than ever with our on demand EV charging stations", "Our EV charging stations are reliable, fast, and compatible with all modern electric "
                             "vehicles.", "/static/assets/product_icons/evcharging.png"),
    ("Smart home energy management", "Connect and optimise your energy usage with our smart home energy mangement"
                                     "systems", "Our smart home energy systems optimise electricity usage and provide "
                                     "intelligent device control.", "/static/assets/product_icons/smarthome.png"),
]

cursor.executemany("""
INSERT INTO products (type, description, details, image)
VALUES (?, ?, ?, ?)
""", products_data)

connection.commit()
connection.close()
