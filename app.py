from flask import Flask, render_template, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from geopy.distance import geodesic
import statistics
import os

app = Flask(__name__)

# Connect to Render PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define your User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

# Ensure tables exist
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/get_user/<name>", methods=["GET"])
def get_user(name):
    user = User.query.filter_by(name=name).first()
    if user:
        return jsonify({
            "name": user.name,
            "phone": user.phone,
            "latitude": user.latitude,
            "longitude": user.longitude
        })
    return jsonify(None)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    name = data.get("name")
    phone = data.get("phone")
    lat = data["location"]["lat"]
    lon = data["location"]["lng"]

    user = User.query.filter_by(name=name).first()
    if user:
        user.phone = phone
        user.latitude = lat
        user.longitude = lon
    else:
        user = User(name=name, phone=phone, latitude=lat, longitude=lon)
        db.session.add(user)

    db.session.commit()
    return jsonify({"status": "success"})

@app.route("/admin")
def admin():
    users = User.query.all()

    pairings = []
    coords = [(u.name, u.phone, (u.latitude, u.longitude)) for u in users]
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
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
