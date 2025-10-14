import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from geopy.distance import geodesic
import statistics

app = Flask(__name__)
# Secret key for session. In production set SECRET_KEY env var to a strong secret.
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# PostgreSQL on Render (or fallback to SQLite locally)
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

# Initialize DB on startup
with app.app_context():
    db.create_all()

# ---------- ROUTES ----------

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

    # Return JSON including a redirect URL so the client can navigate to the thank-you page
    return jsonify({'status': 'success', 'redirect': url_for('thank_you')})

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
    return jsonify({})

@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # If user posts the password, try to authenticate
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw == '7799':
            session['is_admin'] = True
            return redirect(url_for('admin'))
        # invalid password -> render login with error
        return render_template('admin_login.html', error=True)

    # GET: if not authenticated, show login form
    if not session.get('is_admin'):
        return render_template('admin_login.html', error=False)

    # Authenticated: show dashboard
    users = User.query.all()
    pairings = []
    seen = set()
    for u in users:
        if u.matched_with and u.id not in seen:
            partner = User.query.filter_by(name=u.matched_with).first()
            if partner:
                dist = geodesic((u.latitude, u.longitude), (partner.latitude, partner.longitude)).km
                pairings.append((u.name, u.phone, partner.name, partner.phone, round(dist, 2)))
                seen.add(u.id)
                seen.add(partner.id)
    return render_template('admin.html', users=users, pairings=pairings)




@app.route('/delete/<int:user_id>')
def delete(user_id):
    # Only allow deletion when logged in as admin
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin'))


@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

# ---------- RUN APP ----------
if __name__ == '__main__':
    app.run(debug=True)
