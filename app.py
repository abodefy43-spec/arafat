import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from geopy.distance import geodesic
import statistics

app = Flask(__name__)

# PostgreSQL on Render (fallback to SQLite locally)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///users.db'
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

# Initialize tables
with app.app_context():
    db.create_all()

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Get user by name (for prefill)
@app.route('/get_user/<string:name>')
def get_user(name):
    user = User.query.filter_by(name=name).first()
    if user:
        return jsonify({
            'name': user.name,
            'phone': user.phone,
            'latitude': user.latitude,
            'longitude': user.longitude
        })
    return jsonify(None)

# Form submission
@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    lat = data['location']['lat']
    lng = data['location']['lng']

    # Check if user exists
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
                    # Pair users
                    user.matched_with = u.name
                    u.matched_with = user.name
                    db.session.commit()
                    break

    return jsonify({'status': 'success'})

# Admin page
@app.route('/admin')
def admin():
    users = User.query.all()
    pairings = []
    seen = set()
    for u in users:
        if u.matched_with and (u.id, u.matched_with) not in seen and (u.matched_with, u.id) not in seen:
            match_user = User.query.filter_by(name=u.matched_with).first()
            if match_user:
                dist = geodesic((u.latitude, u.longitude), (match_user.latitude, match_user.longitude)).km
                pairings.append((u.name, u.phone, match_user.name, match_user.phone, round(dist, 2)))
                seen.add((u.id, match_user.id))
    return render_template('admin.html', users=users, pairings=pairings)

# Delete user
@app.route('/delete/<int:user_id>')
def delete(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
