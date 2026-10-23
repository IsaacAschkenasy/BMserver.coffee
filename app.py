import os
from html import escape
from html.parser import HTMLParser
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from markupsafe import Markup
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

class MessageHTMLSanitizer(HTMLParser):
    allowed_tags = {"b", "strong", "i", "em", "ul", "li", "br", "p", "div"}
    void_tags = {"br"}
    blocked_tags = {"script", "style"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.open_tags = []
        self.blocked_depth = 0

    def handle_starttag(self, tag, _attrs):
        del _attrs
        if tag in self.blocked_tags:
            self.blocked_depth += 1
            return
        if self.blocked_depth:
            return
        if tag not in self.allowed_tags:
            return
        self.parts.append(f"<{tag}>")
        if tag not in self.void_tags:
            self.open_tags.append(tag)

    def handle_endtag(self, tag):
        if tag in self.blocked_tags and self.blocked_depth:
            self.blocked_depth -= 1
            return
        if self.blocked_depth:
            return
        if tag not in self.allowed_tags or tag in self.void_tags or tag not in self.open_tags:
            return
        while self.open_tags:
            open_tag = self.open_tags.pop()
            self.parts.append(f"</{open_tag}>")
            if open_tag == tag:
                break

    def handle_data(self, data):
        if self.blocked_depth:
            return
        self.parts.append(escape(data, quote=False))

    def get_html(self):
        while self.open_tags:
            self.parts.append(f"</{self.open_tags.pop()}>")
        return "".join(self.parts).strip()

def sanitize_message(value):
    sanitizer = MessageHTMLSanitizer()
    sanitizer.feed(value)
    sanitizer.close()
    return sanitizer.get_html()

def message_has_text(value):
    sanitizer = MessageHTMLSanitizer()
    sanitizer.feed(value)
    sanitizer.close()
    return "".join(
        part for part in sanitizer.parts if not part.startswith("<")
    ).strip()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY,
                text TEXT)
            ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS donors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                donor_name TEXT NOT NULL,
                message TEXT NOT NULL)
            ''')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM content")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO content (id, text) VALUES (1, 'Welcome to the display screen!')")

def get_current_data():
    return "current data"

def get_donors():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        donors = conn.execute(
            "SELECT id, type, donor_name, message FROM donors ORDER BY id"
        ).fetchall()
    return [
        {
            "id": donor["id"],
            "type": donor["type"],
            "donor_name": donor["donor_name"],
            "message": Markup(sanitize_message(donor["message"])),
        }
        for donor in donors
    ]

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
    return render_template(
        'admin.html',
        donors=get_donors(),
    )

@app.route('/admin/create', methods=['POST'])
def create_donor():
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    donor_type = (request.form.get('type') or '').strip()
    donor_name = (request.form.get('donor_name') or '').strip()
    raw_message = request.form.get('message') or ''
    message = sanitize_message(raw_message)
    if not donor_type or not donor_name or not message_has_text(raw_message):
        return jsonify({
            "success": False,
            "error": "Type, donor name, and message are required.",
        }), 400

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO donors (type, donor_name, message) VALUES (?, ?, ?)",
            (donor_type, donor_name, message),
        )

    return jsonify({"success": True}), 201

@app.route('/admin/donors/<int:donor_id>/update', methods=['POST'])
def update_donor(donor_id):
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    donor_type = (request.form.get('type') or '').strip()
    donor_name = (request.form.get('donor_name') or '').strip()
    raw_message = request.form.get('message') or ''
    message = sanitize_message(raw_message)
    if not donor_type or not donor_name or not message_has_text(raw_message):
        return jsonify({
            "success": False,
            "error": "Type, donor name, and message are required.",
        }), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            UPDATE donors
            SET type = ?, donor_name = ?, message = ?
            WHERE id = ?
            """,
            (donor_type, donor_name, message, donor_id),
        )
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "Donor not found."}), 404

    return jsonify({"success": True})

@app.route('/admin/donors/<int:donor_id>/delete', methods=['POST'])
def delete_donor(donor_id):
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM donors WHERE id = ?", (donor_id,))
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "Donor not found."}), 404

    return jsonify({"success": True})

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