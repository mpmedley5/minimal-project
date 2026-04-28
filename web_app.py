"""
Flask Web Application - CompTIA Domain Knowledge Chatbot
Chunk 7: Backend Scalability with SQL Database and ORM Integration

This module provides a Flask web server with:
- Domain selection with session persistence
- Interactive chatbot interface for asking questions
- SQL database backend with SQLAlchemy ORM for scalable data management
"""

import json
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Work around newer werkzeug releases which no longer expose __version__
# (Flask's test client attempts to read it). Add a synthetic value if missing.
import werkzeug
if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '0.0'

from flask import Flask, render_template, render_template_string, request, jsonify, session, redirect, flash, get_flashed_messages
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# Import database models and SQLAlchemy
from models import db, User, ChatSession, Message

# Create Flask application instance
app = Flask(__name__)

# Load configuration from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

db_url = os.getenv("DATABASE_URL")
if db_url:
    # Fix Render/Postgres URL for SQLAlchemy psycopg driver
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # Local development fallback (DO NOT REMOVE)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///local.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Initialize SQLAlchemy with the app
db.init_app(app)

# Database tables will be created when the app starts (see below)

# File paths for data persistence (legacy - to be deprecated)
QA_FILE = "qa_conversations.json"  # legacy storage, still around
CHATS_FILE = "chats.json"           # new structured chat sessions
ACTIVITY_FILE = "activity_log.json"  # records each question/answer
DOMAIN_DATA_FILE = "domain_data.json"

# Available domains
DOMAINS = [
    "CompTIA A+ Hardware",
    "CompTIA A+ Software",
    "CompTIA Network+",
    "CompTIA Security+",
    "CompTIA Linux+",
    "CompTIA Pentest+",
    "CompTIA CySA+",
    "CompTIA SecAI+",
]

# Logos removed: using text-only domain cards for now
LOGOS = {}

# Snow College Color Palette
COLORS = {
    "badger_blue": "#1E376C",      # Primary color
    "snow_orange": "#F47920",       # Secondary color
    "gray": "#939598",              # Neutral color
    "light_orange": "#FAA634"       # Accent color
}



# ---- user management helpers ----

def find_user_by_email(email):
    """Look up a user by email address (case-insensitive)."""
    normalized_email = email.strip().lower()
    return User.query.filter(User.email.ilike(normalized_email)).first()

def create_user(first_name, last_name, email, password_hash):
    """Create a new user in the database."""
    user = User(
        id=str(uuid4()),
        first_name=first_name,
        last_name=last_name,
        email=email.lower(),
        password_hash=password_hash
    )
    db.session.add(user)
    db.session.commit()
    return user

def update_user_last_login(user):
    """Update the user's last login timestamp."""
    user.last_login = datetime.utcnow()
    db.session.commit()


# ---- end user helpers ----

def load_domain_data():
    """Load domain descriptions from JSON file and normalize legacy list formats."""
    if os.path.exists(DOMAIN_DATA_FILE):
        try:
            with open(DOMAIN_DATA_FILE, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            merged = {}
            for item in data:
                if isinstance(item, dict):
                    merged.update(item)
            return merged
        return {}
    return {}


def load_conversations():
    """Load conversations from legacy QA file."

    This function is no longer used by new chat logic but retained
    for backwards compatibility with earlier chunks.
    """
    if os.path.exists(QA_FILE):
        try:
            with open(QA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_conversations(conversations):
    """Save to the legacy QA file (unused by new code)."""
    try:
        with open(QA_FILE, 'w') as f:
            json.dump(conversations, f, indent=2)
    except IOError:
        pass


# --- activity logging helpers ---

def log_activity(entry):
    """Append a single activity record to disk."""
    activities = []
    if os.path.exists(ACTIVITY_FILE):
        try:
            with open(ACTIVITY_FILE, 'r') as f:
                activities = json.load(f)
        except (json.JSONDecodeError, IOError):
            activities = []
    activities.append(entry)
    try:
        with open(ACTIVITY_FILE, 'w') as f:
            json.dump(activities, f, indent=2)
    except IOError:
        pass

# --- chat session helpers ---

def get_user_chats(user_id):
    """Get all chat sessions for a user."""
    return ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.last_updated.desc()).all()

def get_chat_by_id(chat_id, user_id=None):
    """Get a chat session by ID, optionally restricted to a specific user."""
    query = ChatSession.query.filter_by(id=chat_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    return query.first()


def get_current_user():
    """Return the currently authenticated user or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.filter_by(id=user_id).first()


def create_chat_session(user_id, domain_id, chat_name):
    """Create a new chat session in the database."""
    chat = ChatSession(
        id=str(uuid4()),
        user_id=user_id,
        domain_id=domain_id,
        chat_name=chat_name
    )
    db.session.add(chat)
    db.session.commit()
    return chat

def add_message_to_chat(chat_id, role, content):
    """Add a message to a chat session."""
    message = Message(
        id=str(uuid4()),
        chat_id=chat_id,
        role=role,
        content=content
    )
    db.session.add(message)
    # Update the chat's last_updated timestamp
    chat = ChatSession.query.filter_by(id=chat_id).first()
    if chat:
        chat.last_updated = datetime.utcnow()
    return message


def get_domain_description(domain):
    """Get the description for a specific domain."""
    domain_data = load_domain_data()
    return domain_data.get(domain, "Domain information not available.")


# authentication and session helpers

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id') or not get_current_user():
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


def is_strong_password(password):
    """Validate password strength for user registration."""
    if len(password) < 10:
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/~`" for c in password):
        return False
    return True


# --- dashboard rendering --------------------------------------------------

def render_dashboard(user_chats, active_chat=None):
    """Return HTML for the main interface with sidebar and domain grid or chat.

    Args:
        user_chats (list): list of ChatSession objects belonging to the current user.
        active_chat (ChatSession|None): which chat is currently open; if None show
            domain grid on the right.
    """
    domain_data = load_domain_data()
    messages = get_flashed_messages()

    # sidebar chat list items with domain data attribute for filtering
    list_items = ''
    for c in user_chats:
        when = c.last_updated.isoformat() if c.last_updated else c.created_at.isoformat()
        when = when[:10]  # just date
        domain_id = c.domain_id
        list_items += (
            f"<li data-domain=\"{domain_id}\"><a href=\"/load_chat/{c.id}\">"
            f"{c.domain_id} | {c.chat_name} | {when}</a></li>"
        )

    # domain dropdown with "All Chats" option
    dropdown = '<select id="domainSelect" onchange="filterChatsByDomain()">'
    dropdown += '<option value="">All Chats</option>'
    for d in DOMAINS:
        dropdown += f'<option value="{d}">{d}</option>'
    dropdown += '</select>'

    # controls with new chat button and chat history link
    controls = f"""
    {dropdown}
    <button onclick="startNewChat()">New Chat</button>
    <button onclick="window.location.href='/chat_history'" style="margin-top:0.5rem; padding:0.5rem 1rem; background:{COLORS['badger_blue']}; color:white; border:none; border-radius:4px; cursor:pointer; font-size:0.9rem;">View Chat History</button>
    """

    # right panel content - either domain grid or active chat
    if active_chat:
        messages_html = ''
        # Get messages for this chat
        chat_messages = Message.query.filter_by(chat_id=active_chat.id).order_by(Message.timestamp).all()
        for m in chat_messages:
            cls = 'user' if m.role == 'student' else 'bot'
            # escape content for safety
            content = m.content.replace('<','&lt;').replace('>','&gt;')
            action_buttons = ''
            if m.role == 'student':
                action_buttons = f'<div style="margin-top:5px; text-align:right;"><a href="/edit_message/{m.id}" style="background:#F47920; color:white; border:none; padding:2px 5px; border-radius:3px; font-size:0.8em; text-decoration:none; margin-right:5px;">Edit</a><form method="POST" action="/delete_message/{m.id}" style="display:inline;"><button type="submit" onclick="return confirm(\'Are you sure you want to delete this message?\')" style="background:#dc3545; color:white; border:none; padding:2px 5px; border-radius:3px; font-size:0.8em; cursor:pointer;">Delete</button></form></div>'
            messages_html += (
                f"<div class=\"message {cls}\">"
                f"<div class=\"message-content\">{content}</div>"
                f"{action_buttons}"
                f"</div>"
            )
        main_content = f"""
            <div class="domain-info">
                <p><strong>Domain Focus:</strong> {get_domain_description(active_chat.domain_id)}</p>
            </div>
            <div class="messages" id="messages">
                {messages_html}
            </div>
            <div class="input-area">
                <input type="text" id="questionInput" placeholder="Ask a question about {active_chat.domain_id}..." onkeypress="handleKeyPress(event)">
                <button onclick="sendQuestion()">Send</button>
            </div>
            <div class="actions">
                <button onclick="backToDomains()">Back to Domains</button>
            </div>
        """
    else:
        # Show domain grid
        domain_buttons = ""
        for domain in DOMAINS:
            description = domain_data.get(domain, "Domain information")
            domain_buttons += f"""
            <button class="domain-button" onclick="selectDomain('{domain}')">
                <div class='domain-text'>
                    <strong>{domain}</strong>
                    <p class="domain-desc">{description}</p>
                </div>
            </button>
            """
        main_content = f"""
            <div class="welcome-section">
                <h2>Select a Domain to Continue</h2>
                <p>
                    Choose a CompTIA certification domain below to begin your interactive study session.
                    A new chat will be created for you once you make a selection.
                </p>
            </div>
            <div class="domains-grid">
                {domain_buttons}
            </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - CompTIA Knowledge Companion</title>
        <style>
            body {{ margin:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; height:100vh; display:flex; flex-direction:column; }}
            header {{ background-color: {COLORS['badger_blue']}; color: white; padding:1.5rem 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); position:relative; }}
            header h1 {{ margin:0; font-size:1.8rem; }}
            header p {{ margin:0; font-size:0.95rem; color:{COLORS['light_orange']}; }}
            .main-wrapper {{ display:flex; flex:1; }}
            .sidebar {{ width:25%; background:#f0f4f8; border-right:1px solid #ddd; padding:1rem; display:flex; flex-direction:column; overflow-y:auto; }}
            .sidebar h2 {{ font-size:1.1rem; margin:0 0 0.5rem 0; color:{COLORS['badger_blue']}; }}
            .sidebar ul {{ list-style:none; padding:0; margin:0 0 1rem 0; overflow-y:auto; flex:1; }}
            .sidebar li {{ margin-bottom:0.5rem; }}
            .sidebar a {{ text-decoration:none; color:#333; font-size:0.9rem; display:block; padding:0.5rem; border-radius:4px; word-break:break-word; }}
            .sidebar a:hover {{ background:{COLORS['badger_blue']}; color:white; }}
            .sidebar .controls {{ margin-bottom:1rem; padding-top:0.5rem; border-top:1px solid #ccc; }}
            .sidebar select {{ width:100%; padding:0.5rem; margin-bottom:0.5rem; }}
            .sidebar button {{ width:100%; padding:0.5rem; background:{COLORS['badger_blue']}; color:white; border:none; border-radius:4px; cursor:pointer; }}
            .main-panel {{ flex:1; display:flex; flex-direction:column; overflow-y:auto; padding:2rem; }}
            .welcome-section {{ margin-bottom:2rem; }}
            .welcome-section h2 {{ color:{COLORS['badger_blue']}; margin-bottom:1rem; font-size:1.8rem; border-left:4px solid {COLORS['snow_orange']}; padding-left:1rem; }}
            .welcome-section p {{ color:#555; margin-bottom:1rem; font-size:1.05rem; }}
            .domains-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin: 1.5rem 0; }}
            .domain-button {{ background-color: #f9f9f9; border: 1px solid {COLORS['gray']}; border-radius: 6px; padding: 1.5rem; min-height: 140px; cursor: pointer; transition: all 0.2s ease; text-align: center; font-size: 0.9rem; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem; }}
            .domain-button:hover {{ background-color: {COLORS['badger_blue']}; color: white; border-color: {COLORS['snow_orange']}; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
            .domain-text {{ display: flex; flex-direction: column; align-items: center; }}
            .domain-button strong {{ font-size: 1.2rem; margin-bottom: 0.25rem; line-height: 1.2; }}
            .domain-desc {{ font-size: 0.85rem; opacity: 0.8; margin: 0; line-height: 1.3; }}
            .domain-button:hover .domain-desc {{ opacity: 1; }}
            .domain-info {{ background-color: #f0f4f8; padding:1rem; border-left:4px solid {COLORS['snow_orange']}; margin-bottom:1rem; }}
            .domain-info p {{ margin:0; color:#555; }}
            .messages {{ flex:1; overflow-y:auto; padding:1.5rem; display:flex; flex-direction:column; gap:1rem; }}
            .message {{ display:flex; gap:1rem; }}
            .message.user {{ justify-content:flex-end; }}
            .message-content {{ max-width:70%; padding:1rem; border-radius:8px; word-wrap:break-word; }}
            .message.bot .message-content {{ background:#f0f4f8; border-left:4px solid {COLORS['snow_orange']}; }}
            .message.user .message-content {{ background:{COLORS['badger_blue']}; color:white; }}
            .input-area {{ padding:1rem; border-top:1px solid #eee; display:flex; gap:1rem; }}
            .input-area input {{ flex:1; padding:0.75rem; border:2px solid {COLORS['gray']}; border-radius:4px; }}
            .input-area input:focus {{ outline:none; border-color:{COLORS['badger_blue']}; box-shadow:0 0 0 3px rgba(30, 55, 108, 0.1); }}
            .input-area button {{ padding:0.75rem 1.5rem; background:{COLORS['badger_blue']}; color:white; border:none; border-radius:4px; cursor:pointer; }}
            .input-area button:hover {{ background:{COLORS['snow_orange']}; }}
            .actions {{ padding:1rem; border-top:1px solid #eee; display:flex; gap:1rem; }}
            .actions button {{ padding:0.5rem 1rem; background:#f0f4f8; border:1px solid {COLORS['gray']}; border-radius:4px; cursor:pointer; }}
            .actions button:hover {{ background:{COLORS['badger_blue']}; color:white; }}
        </style>
    </head>
    <body>
        <header>
            <h1>📚 CompTIA Knowledge Companion</h1>
            <p>Your Interactive Study Assistant</p>
            <a href="/logout" style="position:absolute; right:2rem; top:1.5rem; color:white; text-decoration:none; font-size:0.95rem;">Logout</a>
        </header>
    """
    html += """
        {% if messages %}
        <div style="background:#e8f4fd; color:#1E376C; padding:1rem; margin:1rem 2rem; border-left:4px solid #F47920;">
            {% for message in messages %}<p style="margin:0;">{{ message }}</p>{% endfor %}
        </div>
        {% endif %}
    """
    html += f"""
        <div class="main-wrapper">
            <aside class="sidebar">
                <div>
                    <h2>Your Chats</h2>
                    <div class="controls">
                        {controls}
                    </div>
                </div>
                <ul id="chatList">
                    {list_items}
                </ul>
            </aside>
            <main class="main-panel">
                {main_content}
            </main>
        </div>
        <script>
            function startNewChat() {{
                const domain = document.getElementById('domainSelect').value;
                fetch('/new_chat', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{domain:domain}})}})
                .then(r=>r.json()).then(d=>{{ if(d.success) window.location.href='/load_chat/'+d.chat_id; }})
            }}
            function selectDomain(domain) {{
                fetch('/new_chat', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{domain:domain}})}})
                .then(r=>r.json()).then(d=>{{ if(d.success && d.chat_id) window.location.href='/load_chat/'+d.chat_id; }})
                .catch(error => console.error('Error:', error));
            }}
            function handleKeyPress(e) {{ if (e.key==='Enter') sendQuestion(); }}
            function sendQuestion() {{
                const input = document.getElementById('questionInput');
                const q = input.value.trim(); if(!q) return;
                const messagesDiv = document.getElementById('messages');
                const um = document.createElement('div'); um.className='message user'; um.innerHTML=`<div class="message-content">${{q.replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div>`;
                messagesDiv.appendChild(um); input.value=''; messagesDiv.scrollTop=messagesDiv.scrollHeight;
                fetch('/chat',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{question:q}})}})
                .then(r=>r.json()).then(d=>{{
                    if(d.success){{
                        // Add edit/delete buttons to the user message
                        if(d.message_id){{
                            const actionDiv = document.createElement('div');
                            actionDiv.style.marginTop = '5px';
                            actionDiv.style.textAlign = 'right';
                            actionDiv.innerHTML = `<a href="/edit_message/${{d.message_id}}" style="background:#F47920; color:white; border:none; padding:2px 5px; border-radius:3px; font-size:0.8em; text-decoration:none; margin-right:5px;">Edit</a><form method="POST" action="/delete_message/${{d.message_id}}" style="display:inline;"><button type="submit" onclick="return confirm('Are you sure you want to delete this message?')" style="background:#dc3545; color:white; border:none; padding:2px 5px; border-radius:3px; font-size:0.8em; cursor:pointer;">Delete</button></form>`;
                            um.appendChild(actionDiv);
                        }}
                        const bm=document.createElement('div');bm.className='message bot';bm.innerHTML=`<div class="message-content">${{d.response.replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div>`;
                        messagesDiv.appendChild(bm);messagesDiv.scrollTop=messagesDiv.scrollHeight;
                    }}
                }})
            }}
            function backToDomains() {{ window.location.href='/back_to_domains'; }}
            function filterChatsByDomain() {{
                const selectedDomain = document.getElementById('domainSelect').value;
                const chatItems = document.querySelectorAll('#chatList li');
                chatItems.forEach(item => {{
                    const itemDomain = item.getAttribute('data-domain');
                    if (selectedDomain === '' || itemDomain === selectedDomain) {{
                        item.style.display = 'block';
                    }} else {{
                        item.style.display = 'none';
                    }}
                }});
            }}
        </script>
        <footer style="text-align:center; padding:2rem; color:#999; font-size:0.9rem; border-top:1px solid #eee; margin-top:2rem;">
            <p>Built with <span style="font-size:0.85rem; color:{COLORS['badger_blue']}; font-weight:600;">❄️ Snow College</span> academic standards</p>
        </footer>
    </body>
    </html>
    """
    return render_template_string(html, messages=messages)


@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    chats = get_user_chats(user_id)
    active_id = session.get('active_chat_id')
    active_chat = get_chat_by_id(active_id, user_id) if active_id else None
    if active_id and not active_chat:
        session.pop('active_chat_id', None)
        session.pop('selected_domain', None)
    return render_dashboard(chats, active_chat)


@app.route('/back_to_domains')
@login_required
def back_to_domains():
    """Clear active chat and show domain grid."""
    session.pop('active_chat_id', None)
    user_id = session.get('user_id')
    chats = get_user_chats(user_id)
    return render_dashboard(chats, active_chat=None)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        first = request.form.get('first_name', '').strip()
        last = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        passwd = request.form.get('password', '')
        if not first or not last:
            error = 'First and last name are required.'
        elif not email or not email.lower().endswith('@snow.edu'):
            error = 'Email must end with @snow.edu.'
        elif find_user_by_email(email):
            error = 'Email already registered.'
        elif not is_strong_password(passwd):
            error = 'Password must be at least 10 characters and include uppercase, lowercase, digits, and symbols.'
        else:
            pwd_hash = generate_password_hash(passwd)
            create_user(first, last, email, pwd_hash)
            return redirect('/login')
    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        passwd = request.form.get('password', '')
        user = find_user_by_email(email)
        if not user or not check_password_hash(user.password_hash, passwd):
            error = 'Invalid credentials.'
        else:
            session.clear()
            session.permanent = True
            session['user_id'] = user.id
            update_user_last_login(user)
            flash(f'Welcome back, {user.first_name}!')
            return redirect('/dashboard')
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route("/init-db")
def init_db():
    from models import db
    with app.app_context():
        db.create_all()
    return "Database initialized!"


@app.route("/")
@login_required
def index():
    """
    Root route handler (authenticated) - Domain selection page.

    Returns:
        str: HTML response with clickable domain selection or redirect to login
    """
    current_domain = session.get('selected_domain', None)
    domain_data = load_domain_data()
    logout_link = '<a href="/logout" style="position:absolute;top:1rem;right:1rem;color:white;">Logout</a>' if 'user_id' in session else ''
    
    domain_buttons = ""
    for domain in DOMAINS:
        description = domain_data.get(domain, "Domain information")
        domain_buttons += f"""
        <button class="domain-button" onclick="selectDomain('{domain}')">
            <div class='domain-text'>
                <strong>{domain}</strong>
                <p class="domain-desc">{description}</p>
            </div>
        </button>
        """
    
    selected_display = f"<p class='status-message'>Currently studying: <strong>{current_domain}</strong></p>" if current_domain else ""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CompTIA Knowledge Companion</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                color: #333;
                line-height: 1.6;
            }}
            
            header {{
                background-color: {COLORS['badger_blue']};
                color: white;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            header h1 {{
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                font-weight: 700;
                letter-spacing: -1px;
            }}
            
            header p {{
                font-size: 1.1rem;
                color: {COLORS['light_orange']};
                opacity: 0.95;
            }}
            
            .container {{
                max-width: 1000px;
                margin: 2rem auto;
                padding: 2rem;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            
            .welcome-section {{
                margin-bottom: 2rem;
            }}
            
            .welcome-section h2 {{
                color: {COLORS['badger_blue']};
                margin-bottom: 1rem;
                font-size: 1.8rem;
                border-left: 4px solid {COLORS['snow_orange']};
                padding-left: 1rem;
            }}
            
            .welcome-section p {{
                color: #555;
                margin-bottom: 1rem;
                font-size: 1.05rem;
            }}
            
            .status-message {{
                background-color: #e8f5e9;
                border-left: 4px solid {COLORS['snow_orange']};
                padding: 1rem;
                border-radius: 4px;
                color: #2e7d32;
                margin-bottom: 1.5rem;
            }}
            
            .domains-grid {{
                display: grid;
                /* more columns for streaming multiple domains */
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 0.75rem;
                margin: 1.5rem 0;
            }}
            
            .domain-button {{
                background-color: #f9f9f9;
                border: 1px solid {COLORS['gray']};
                border-radius: 6px;
                padding: 1.5rem;
                min-height: 140px;
                cursor: pointer;
                transition: all 0.2s ease;
                text-align: center;
                font-size: 0.9rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
            }}
            
            .domain-button:hover {{
                background-color: {COLORS['badger_blue']};
                color: white;
                border-color: {COLORS['snow_orange']};
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            
            /* .domain-logo rules removed (text-only cards) */
            .domain-text {{
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .domain-button strong {{
                font-size: 1.2rem;
                margin-bottom: 0.25rem;
                line-height: 1.2;
            }}
            
            .domain-desc {{
                font-size: 0.85rem;
                opacity: 0.8;
                margin: 0;
                line-height: 1.3;
            }}
            
            .domain-button:hover .domain-desc {{
                opacity: 1;
            }}
            
            footer {{
                text-align: center;
                padding: 2rem;
                color: #999;
                font-size: 0.9rem;
                border-top: 1px solid #eee;
                margin-top: 2rem;
            }}
            
            .snow-college-badge {{
                font-size: 0.85rem;
                color: {COLORS['badger_blue']};
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>📚 CompTIA Knowledge Companion</h1>
            <p>Your Interactive Study Assistant for CompTIA Certification Domains</p>
            {logout_link}
        </header>
        
        <div class="container">
            <div class="welcome-section">
                <h2>Select a Domain to Continue</h2>
                <p>
                    Choose a CompTIA certification domain below to begin your interactive study session.
                    A new chat will be created for you once you make a selection.
                </p>
            </div>
            
            {selected_display}
            
            <div class="domains-grid">
                {domain_buttons}
            </div>
        </div>
        
        <footer>
            <p>Built with <span class="snow-college-badge">❄️ Snow College</span> academic standards</p>
        </footer>
        
        <script>
            function selectDomain(domain) {{
                // create a new chat for this domain and navigate to it
                fetch('/new_chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{domain: domain}})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success && data.chat_id) {{
                        window.location.href = '/load_chat/' + data.chat_id;
                    }}
                }})
                .catch(error => console.error('Error:', error));
            }}
        </script>
    </body>
    </html>
    """
    return html_content


@app.route("/set_domain", methods=["POST"])
@login_required
def set_domain():
    """
    API endpoint to set the selected domain in the session.
    
    Returns:
        JSON: Success response
    """
    data = request.get_json()
    selected_domain = data.get('domain')
    
    if selected_domain in DOMAINS:
        session['selected_domain'] = selected_domain
        return jsonify({"success": True, "domain": selected_domain})
    
    return jsonify({"success": False, "error": "Invalid domain"}), 400





@app.route("/new_chat", methods=["POST"])
@login_required
def new_chat():
    """Create a new chat session for the logged‑in student."""
    data = request.get_json() or {}
    domain = data.get('domain')
    if domain not in DOMAINS:
        return jsonify({"success": False, "error": "Invalid domain"}), 400

    user_id = session.get('user_id')
    now = datetime.now().isoformat()
    chat_name = f"{domain} chat {now[:16]}"  # short timestamp
    chat = create_chat_session(user_id, domain, chat_name)

    # set session pointers
    session['active_chat_id'] = chat.id
    session['selected_domain'] = domain
    return jsonify({"success": True, "chat_id": chat.id})


@app.route("/load_chat/<chat_id>")
@login_required
def load_chat(chat_id):
    """Render the dashboard with a particular chat loaded."""
    user_id = session.get('user_id')
    chat = get_chat_by_id(chat_id, user_id)
    if not chat:
        return "Chat not found or access denied", 404

    # set current context
    session['active_chat_id'] = chat_id
    session['selected_domain'] = chat.domain_id
    chats = get_user_chats(user_id)
    return render_dashboard(chats, active_chat=chat)


@app.route("/chat", methods=["GET"])
@login_required
def chat_redirect():
    # legacy GET endpoint; send user to dashboard where chats live
    return redirect('/dashboard')


@app.route("/chat", methods=["POST"])
@login_required
def ask_question():
    """Handle submission of a question within the currently active chat.

    The POST body should contain {question: str}.
    """
    user_id = session.get('user_id')
    active_id = session.get('active_chat_id')
    if not active_id:
        return jsonify({"success": False, "error": "No active chat"}), 400

    data = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"success": False, "error": "Question cannot be empty"}), 400

    # locate chat record and enforce ownership
    chat = get_chat_by_id(active_id, user_id)
    if not chat:
        return jsonify({"success": False, "error": "Chat not found or access denied"}), 404

    domain = chat.domain_id
    response = generate_response(question, domain)

    # add message entries to database
    user_message = add_message_to_chat(active_id, "student", question)
    add_message_to_chat(active_id, "assistant", response)
    db.session.commit()

    # log the interaction for analytics
    timestamp = datetime.now().isoformat()
    activity = {
        "user_id": session.get('user_id'),
        "chat_id": active_id,
        "domain_id": domain,
        "question": question,
        "response": response,
        "timestamp": timestamp
    }
    log_activity(activity)

    return jsonify({"success": True, "response": response, "message_id": user_message.id, "chat_id": active_id})


@app.route('/chat_history')
@login_required
def chat_history():
    """Display the user's chat history using Jinja2 template."""
    user_id = session.get('user_id')
    user_chats = get_user_chats(user_id)
    return render_template('chat_history.html', chats=user_chats)


@app.route('/edit/<chat_id>', methods=['GET', 'POST'])
@login_required
def edit_chat(chat_id):
    """Edit an existing chat session."""
    user_id = session.get('user_id')
    chat = get_chat_by_id(chat_id, user_id)
    if not chat:
        flash('Unauthorized access')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        new_name = request.form.get('chat_name', '').strip()
        if new_name:
            chat.chat_name = new_name
            db.session.commit()
            flash('Chat updated successfully')
            return redirect('/chat_history')
        else:
            flash('Chat name cannot be empty')
    
    return render_template('edit_chat.html', chat=chat)


@app.route('/delete/<chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    """Delete a chat session."""
    user_id = session.get('user_id')
    chat = get_chat_by_id(chat_id, user_id)
    if not chat:
        flash('Unauthorized access')
        return redirect('/dashboard')
    
    db.session.delete(chat)
    db.session.commit()
    flash('Chat deleted successfully')
    return redirect('/chat_history')


@app.route('/delete_message/<message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete a specific message."""
    user_id = session.get('user_id')
    message = Message.query.filter_by(id=message_id).first()
    if not message:
        flash('Message not found')
        return redirect('/dashboard')
    
    # Verify the message belongs to a chat owned by the user
    chat = ChatSession.query.filter_by(id=message.chat_id, user_id=user_id).first()
    if not chat:
        flash('Unauthorized access')
        return redirect('/dashboard')
    
    # If deleting a user message, also delete the following AI response
    if message.role == 'student':
        next_message = Message.query.filter_by(chat_id=message.chat_id).filter(Message.timestamp > message.timestamp).order_by(Message.timestamp).first()
        if next_message and next_message.role == 'assistant':
            db.session.delete(next_message)
    
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully')
    return redirect(f'/load_chat/{message.chat_id}')


@app.route('/edit_message/<message_id>', methods=['GET', 'POST'])
@login_required
def edit_message(message_id):
    """Edit a specific message."""
    user_id = session.get('user_id')
    message = Message.query.filter_by(id=message_id).first()
    if not message:
        flash('Message not found')
        return redirect('/dashboard')
    
    # Verify the message belongs to a chat owned by the user and is a student message
    chat = ChatSession.query.filter_by(id=message.chat_id, user_id=user_id).first()
    if not chat or message.role != 'student':
        flash('Unauthorized access')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        new_content = request.form.get('message_content', '').strip()
        if new_content:
            old_content = message.content
            message.content = new_content
            # Don't update timestamp for user message to preserve conversation order
            
            # Find the next message (should be the AI response)
            next_message = Message.query.filter_by(chat_id=message.chat_id).filter(Message.timestamp > message.timestamp).order_by(Message.timestamp).first()
            
            if next_message and next_message.role == 'assistant':
                # Re-generate the AI response for the updated question
                domain_data = load_domain_data()
                new_response = generate_response(new_content, chat.domain_id)
                next_message.content = new_response
                next_message.timestamp = datetime.utcnow()  # Update AI response timestamp
            
            db.session.commit()
            flash('Message updated successfully')
            return redirect(f'/load_chat/{message.chat_id}')
        else:
            flash('Message content cannot be empty')
    
    return render_template('edit_message.html', message=message)


# ---- API routes ----

@app.route('/api/v1/items', methods=['GET'])
def api_get_items():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized access"}), 401
    chats = ChatSession.query.filter_by(user_id=user_id).all()
    items = []
    for chat in chats:
        items.append({
            "id": chat.id,
            "domain_id": chat.domain_id,
            "chat_name": chat.chat_name,
            "created_at": chat.created_at.isoformat() if chat.created_at else None,
            "last_updated": chat.last_updated.isoformat() if chat.last_updated else None
        })
    return jsonify(items), 200


@app.route('/api/v1/items/<int:item_id>', methods=['GET'])
def api_get_item(item_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized access"}), 401
    chat = ChatSession.query.filter_by(id=item_id, user_id=user_id).first()
    if not chat:
        return jsonify({"error": "Item not found"}), 404
    item = {
        "id": chat.id,
        "domain_id": chat.domain_id,
        "chat_name": chat.chat_name,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "last_updated": chat.last_updated.isoformat() if chat.last_updated else None
    }
    return jsonify(item), 200


def load_specialized_content(domain):
    """Load specialized content for a domain if it exists."""
    # Normalize domain name for filename
    # "CompTIA Network+" -> "network_plus_content.json"
    domain_name = domain.replace("CompTIA ", "").lower().replace("+", "_plus").replace(" ", "_")
    normalized = domain_name + "_content.json"
    
    if os.path.exists(normalized):
        try:
            with open(normalized, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def find_matching_topic(question, specialized_content, domain):
    """
    Find relevant topics in specialized content based on question keywords.
    
    Args:
        question: The user's question
        specialized_content: Loaded content dict
        domain: The domain name
    
    Returns:
        tuple: (topic_title, topic_content) or (None, None)
    """
    if not specialized_content or domain not in specialized_content:
        return None, None
    
    question_lower = question.lower()
    domain_topics = specialized_content[domain].get("topics", {})
    
    # Search for matching topics by keyword
    best_match = None
    best_match_count = 0
    
    for topic_id, topic_data in domain_topics.items():
        keywords = topic_data.get("keywords", [])
        match_count = sum(1 for kw in keywords if kw in question_lower)
        
        if match_count > best_match_count:
            best_match = topic_data
            best_match_count = match_count
    
    if best_match:
        return best_match.get("title"), best_match.get("content")
    return None, None


def generate_response(question, domain):
    """
    Generate an intelligent response based on the question and domain.
    Uses specialized content files when available (e.g., network_plus_content.json).
    Falls back to generic domain info if specialized content unavailable.
    
    Args:
        question: The user's question
        domain: The selected domain
    
    Returns:
        str: A detailed response about the topic
    """
    # Try to load specialized content for this domain
    specialized_content = load_specialized_content(domain)
    
    if specialized_content:
        topic_title, topic_content = find_matching_topic(question, specialized_content, domain)
        if topic_content:
            question_lower = question.lower()
            # Vary response structure based on question type
            if any(kw in question_lower for kw in ['what', 'tell', 'explain', 'define']):
                return f"**{topic_title}**\n\n{topic_content}\n\nWould you like to know more about related topics in {domain}?"
            elif any(kw in question_lower for kw in ['how', 'why', 'when']):
                return f"Regarding your question about {topic_title}:\n\n{topic_content}\n\nFeel free to ask follow-up questions!"
            else:
                return f"That's a great question! Here's what you should know about {topic_title}:\n\n{topic_content}"
    
    # Fallback to generic response using domain overview
    domain_data = load_domain_data()
    domain_info = domain_data.get(domain, "")
    question_lower = question.lower()
    
    if any(keyword in question_lower for keyword in ['what', 'tell', 'explain', 'define']):
        return f"Great question! In {domain}, {domain_info.lower()} Feel free to ask more specific questions about this topic!"
    elif any(keyword in question_lower for keyword in ['how', 'why', 'when']):
        return f"Regarding '{question}': This relates to {domain}. {domain_info} Would you like to explore a specific aspect further?"
    else:
        return f"Interesting question about {domain}! {domain_info} This is an important concept. Would you like me to explain any specific part?"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
