import os
import json
import re
import tempfile
from html import escape
from html.parser import HTMLParser
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from markupsafe import Markup
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# A secure, unpredictable secret key is generated automatically on startup
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

if os.path.exists('/app'):
    DB_PATH = '/app/data/data.db'
else:
<<<<<<< HEAD
    DB_PATH = os.path.join(os.getcwd(), 'data.db')
SETTINGS_PATH = os.environ.get(
    "SETTINGS_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json"),
)

def default_settings():
    return {
        "display_title": "Coffee Display",
        "background_color": "#f4f4f4",
        "background_opacity": 0.9,
        "refresh_interval": 30,
        "admin_username": os.environ.get("ADMIN_USER", "admin"),
        "admin_password_hash": generate_password_hash(
            os.environ.get("ADMIN_PASS", "ChangeMe123!")
        ),
    }

def validate_settings(settings):
    if not isinstance(settings, dict):
        raise ValueError("Settings file must contain a JSON object.")
    required = {
        "display_title": str,
        "background_color": str,
        "background_opacity": (int, float),
        "refresh_interval": int,
        "admin_username": str,
        "admin_password_hash": str,
    }
    for key, expected_type in required.items():
        if not isinstance(settings.get(key), expected_type):
            raise ValueError(f"Invalid setting: {key}")
    if not settings["display_title"].strip():
        raise ValueError("Display title cannot be empty.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", settings["background_color"]):
        raise ValueError("Background color must be a six-digit hex color.")
    if (
        isinstance(settings["background_opacity"], bool)
        or not 0 <= settings["background_opacity"] <= 1
    ):
        raise ValueError("Background opacity must be between 0 and 1.")
    if (
        isinstance(settings["refresh_interval"], bool)
        or not 1 <= settings["refresh_interval"] <= 3600
    ):
        raise ValueError("Refresh interval must be between 1 and 3600 seconds.")
    if not settings["admin_username"].strip() or not settings["admin_password_hash"]:
        raise ValueError("Admin username and password hash cannot be empty.")
    return settings

def load_settings():
    settings = default_settings()
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as settings_file:
                stored_settings = json.load(settings_file)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Could not load settings from {SETTINGS_PATH}") from error
        if not isinstance(stored_settings, dict):
            raise RuntimeError(f"Settings in {SETTINGS_PATH} must be a JSON object.")
        settings.update(stored_settings)
    try:
        return validate_settings(settings)
    except ValueError as error:
        raise RuntimeError(f"Invalid settings in {SETTINGS_PATH}: {error}") from error

def save_settings(settings):
    directory = os.path.dirname(SETTINGS_PATH) or "."
    os.makedirs(directory, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix=".settings-", suffix=".json", dir=directory
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file, ensure_ascii=False, indent=2)
            settings_file.write("\n")
            settings_file.flush()
            os.fsync(settings_file.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, SETTINGS_PATH)
    except OSError:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise

def public_settings():
    return {
        key: settings[key]
        for key in (
            "display_title",
            "background_color",
            "background_opacity",
            "refresh_interval",
            "admin_username",
        )
    }

settings = load_settings()
ADMIN_USERNAME = settings["admin_username"]
ADMIN_PASSWORD_HASH = settings["admin_password_hash"]
=======
    DB_PATH = './data.db'
# Get username and password, default to admin/ChangeMe123! if not set in environment variables
ADMIN_USERNAME = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get("ADMIN_PASS", "ChangeMe123!"))
>>>>>>> f4da0ae50cf44346139296ef70e7df62d289a344

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

@app.route('/admin/settings')
def admin_settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('settings.html', settings=public_settings())

@app.route('/admin/settings/save', methods=['POST'])
def save_admin_settings():
    global settings
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Invalid settings payload."}), 400

    display_title = data.get("display_title")
    background_color = data.get("background_color")
    background_opacity = data.get("background_opacity")
    refresh_interval = data.get("refresh_interval")
    if not isinstance(display_title, str):
        return jsonify({"success": False, "error": "Display title is required."}), 400
    if not isinstance(background_color, str):
        return jsonify({"success": False, "error": "Choose a valid background color."}), 400
    if (
        isinstance(background_opacity, bool)
        or not isinstance(background_opacity, (int, float))
        or not 0 <= background_opacity <= 1
    ):
        return jsonify({"success": False, "error": "Opacity must be between 0 and 1."}), 400
    if (
        isinstance(refresh_interval, bool)
        or not isinstance(refresh_interval, int)
        or not 1 <= refresh_interval <= 3600
    ):
        return jsonify({"success": False, "error": "Refresh interval must be 1–3600 seconds."}), 400

    display_title = display_title.strip()
    if not display_title or len(display_title) > 100:
        return jsonify({"success": False, "error": "Display title is required and may not exceed 100 characters."}), 400
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", background_color):
        return jsonify({"success": False, "error": "Choose a valid background color."}), 400

    updated_settings = {
        **settings,
        "display_title": display_title,
        "background_color": background_color.lower(),
        "background_opacity": float(background_opacity),
        "refresh_interval": refresh_interval,
    }
    try:
        save_settings(updated_settings)
    except OSError:
        app.logger.exception("Could not save settings file")
        return jsonify({"success": False, "error": "Could not save settings. Check server file permissions."}), 500

    settings = updated_settings
    return jsonify({"success": True, "settings": public_settings()})

@app.route('/admin/settings/account/save', methods=['POST'])
def save_admin_account():
    global settings, ADMIN_USERNAME, ADMIN_PASSWORD_HASH
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Invalid account settings payload."}), 400

    admin_username = data.get("admin_username")
    current_password = data.get("current_password")
    new_password = data.get("new_password", "")
    if not isinstance(admin_username, str) or not isinstance(current_password, str) or not isinstance(new_password, str):
        return jsonify({"success": False, "error": "Username and password values must be text."}), 400

    admin_username = admin_username.strip()
    if not admin_username or len(admin_username) > 100:
        return jsonify({"success": False, "error": "Username is required and may not exceed 100 characters."}), 400
    if len(current_password) > 1024 or len(new_password) > 1024:
        return jsonify({"success": False, "error": "Password is too long."}), 400
    if not check_password_hash(ADMIN_PASSWORD_HASH, current_password):
        return jsonify({"success": False, "error": "Current password is incorrect."}), 403
    if new_password and len(new_password) < 8:
        return jsonify({"success": False, "error": "New password must be at least 8 characters."}), 400

    updated_settings = {
        **settings,
        "admin_username": admin_username,
        "admin_password_hash": (
            generate_password_hash(new_password)
            if new_password
            else ADMIN_PASSWORD_HASH
        ),
    }
    try:
        save_settings(updated_settings)
    except OSError:
        app.logger.exception("Could not save account settings")
        return jsonify({"success": False, "error": "Could not save account settings. Check server file permissions."}), 500

    settings = updated_settings
    ADMIN_USERNAME = settings["admin_username"]
    ADMIN_PASSWORD_HASH = settings["admin_password_hash"]
    return jsonify({"success": True, "admin_username": ADMIN_USERNAME})

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