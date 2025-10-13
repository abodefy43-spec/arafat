import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from geopy.distance import geodesic
import statistics

app = Flask(__name__)

# Use the DATABASE_URL from Render environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///users.db'  # fallback for local testing
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    matched_with = db.Column(db.String(200), nullable=True)

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    lat = data['location']['lat']
    lng = data['location']['lng']

    existing = User.query.filter_by(phone=phone).first()
    if existing:
        existing.name = name
        existing.latitude = lat
        existing.longitude = lng
        db.session.commit()
        return jsonify({'status': 'updated'})

    user = User(name=name, phone=phone, latitude=lat, longitude=lng)
    db.session.add(user)
    db.session.commit()

    # Pairing logic (0.5 SD)
    users = User.query.all()
    if len(users) > 1:
        distances = []
        for u in users:
            if u.id == user.id:
                continue
            dist = geodesic((lat, lng), (u.latitude, u.longitude)).km
            distances.append(dist)

        if distances:
            mean_dist = statistics.mean(distances)
            sd_dist = statistics.stdev(distances) if len(distances) > 1 else 0
            for u in users:
                if u.id == user.id:
                    continue
                dist = geodesic((lat, lng), (u.latitude, u.longitude)).km
                if abs(dist - mean_dist) <= 0.5 * sd_dist:
                    user.matched_with = u.name
                    u.matched_with = user.name
                    db.session.commit()
                    break

    return jsonify({'status': 'success'})

@app.route('/admin')
def admin():
    users = User.query.all()
    # Compute pairings for display
    pairings = []
    matched_names = set()
    for u in users:
        if u.matched_with and (u.name, u.matched_with) not in matched_names and (u.matched_with, u.name) not in matched_names:
            other = User.query.filter_by(name=u.matched_with).first()
            if other:
                dist = round(geodesic((u.latitude, u.longitude), (other.latitude, other.longitude)).km, 2)
                pairings.append((u.name, u.phone, other.name, other.phone, dist))
                matched_names.add((u.name, other.name))
    return render_template('admin.html', users=users, pairings=pairings)

@app.route('/delete/<int:user_id>')
def delete(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin'))

# Production-safe database initialization
@app.before_first_request
def create_tables():
    try:
        db.create_all()
    except Exception as e:
        print("Error creating tables:", e)

from geopy.distance import geodesic

@app.route('/admin')
def admin():
    users = User.query.all()
    pairings = []
    matched_names = set()

    for u in users:
        if u.matched_with:
            # Make sure we don’t duplicate pairs
            pair_key = tuple(sorted([u.name, u.matched_with]))
            if pair_key not in matched_names:
                other = User.query.filter_by(name=u.matched_with).first()
                if other:
                    dist = round(geodesic((u.latitude, u.longitude), (other.latitude, other.longitude)).km, 2)
                    pairings.append((u.name, u.phone, other.name, other.phone, dist))
                    matched_names.add(pair_key)

    return render_template('admin.html', users=users, pairings=pairings)


if __name__ == '__main__':
    app.run(debug=True)
