from flask import Flask, render_template, request, jsonify, redirect
import sqlite3
from geopy.distance import geodesic
import statistics

app = Flask(__name__)
DB_PATH = "users.db"

# Initialize database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
)
''')
conn.commit()
conn.close()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/get_user/<name>", methods=["GET"])
def get_user(name):
    """Return existing user data if already submitted"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, phone, latitude, longitude FROM users WHERE name=?", (name,))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({
            "name": user[0],
            "phone": user[1],
            "latitude": user[2],
            "longitude": user[3]
        })
    return jsonify(None)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    name = data.get("name")
    phone = data.get("phone")
    lat = data["location"]["lat"]
    lon = data["location"]["lng"]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE name=?", (name,))
    if c.fetchone():
        # Update existing submission
        c.execute(
            "UPDATE users SET phone=?, latitude=?, longitude=? WHERE name=?",
            (phone, lat, lon, name)
        )
    else:
        # Insert new submission
        c.execute(
            "INSERT INTO users (name, phone, latitude, longitude) VALUES (?, ?, ?, ?)",
            (name, phone, lat, lon)
        )
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, phone, latitude, longitude FROM users")
    users = c.fetchall()
    conn.close()

    # Pairing based on 0.5 standard deviation
    pairings = []
    coords = [(u[1], u[2], (u[3], u[4])) for u in users]  # name, phone, (lat, lon)
    distances = []

    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            dist = geodesic(coords[i][2], coords[j][2]).km
            distances.append(dist)

    if distances:
        mean_dist = statistics.mean(distances)
        stdev_dist = statistics.stdev(distances) if len(distances) > 1 else 0
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                dist = geodesic(coords[i][2], coords[j][2]).km
                if abs(dist - mean_dist) <= 0.5 * stdev_dist:
                    pairings.append((
                        coords[i][0], coords[i][1],
                        coords[j][0], coords[j][1],
                        round(dist, 2)
                    ))

    return render_template("admin.html", users=users, pairings=pairings)

@app.route("/delete/<int:user_id>")
def delete(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
