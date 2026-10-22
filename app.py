import os
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="source")
# A secure, unpredictable secret key is generated automatically on startup
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

if os.path.exists('/app'):
    DB_PATH = '/app/data/data.db'
else:
    DB_PATH = os.path.join(os.getcwd(), 'data.db')
# Get username and password, default to admin/ChangeMe123! if not set in environment variables
ADMIN_USERNAME = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get("ADMIN_PASS", "ChangeMe123!"))

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY,
                text TEXT)
            ''')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM content")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO content (id, text) VALUES (1, 'Welcome to the display screen!')")

def get_current_data():
    return "current data"

# Public Route: Renders display layout
@app.route('/')
def display():
    return render_template('display.html')

# JSON API Route: Allows display.html to fetch the updated message continuously
@app.route('/api/data')
def get_display_data():
    return "diplay_data!!!!!!!!!"

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def authenticate_user():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        session['logged_in'] = True
        return redirect(url_for('admin'))
    else:
        return render_template('login.html', error="Invalid credentials")

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin.html', content=get_current_data())

@app.route('/admin/update', methods=['POST'])
def update_data():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    new_content = request.form.get('content')
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)