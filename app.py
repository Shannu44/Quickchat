from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from datetime import timedelta
from flask import Flask, request, jsonify, session
import pytz
import sqlite3

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '2004'
socketio = SocketIO(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def init_db():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    current_time = datetime.utcnow().isoformat()  # Save in UTC ISO 8601 format


        # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Admins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

        # Messages table (Fixed schema without ALTER TABLE)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            recipient_id INTEGER,
            message TEXT,
            timestamp_utc TEXT
        )
    ''')

    # Recent chats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recent_chats (
            sender_id INTEGER,
            user_id INTEGER,
            timestamp_local TEXT,
            PRIMARY KEY (sender_id, user_id)
        )
    ''')

    # Add timestamp_utc column
    cursor.execute("PRAGMA table_info(messages)")
    columns = [column[1] for column in cursor.fetchall()]
    if "timestamp_utc" not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN timestamp_utc TEXT")

class User(UserMixin):
    def __init__(self, id, username, password, is_admin):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password, is_admin FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[3])
    return None

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', (username, password, 0))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Username already exists.", 400
    finally:
        conn.close()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('chat.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and user[2] == password:  # Direct comparison for plaintext passwords
            login_user(User(user[0], user[1], user[2], user[3]))
            session.permanent = True  # ✅ session persistent
            session['user_id'] = user[0]  # ✅ Store user_id in session
            print(f"User {user[0]} logged in")  # Debugging purpose
            next_page = request.args.get('next')  # Fix the redirect issue
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/debug_session')
def debug_session():
    return jsonify({'user_id': session.get('user_id')})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    next_page = request.args.get('next')  # Fix for next page redirect

    if request.method == 'POST':
        username = request.form['username']  # Changed from admin_username to username
        password = request.form['password']

        # Admin credentials (hardcoded)
        ADMIN_USERNAME = 'admin'  # Hardcoded admin username
        ADMIN_PASSWORD = '1234'  # Hardcoded admin password

        # Check if the entered credentials match the hardcoded ones
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = username  # Store the admin username in the session
            flash("Login successful!", "success")
            return redirect(next_page or url_for('admin_panel'))  # Redirect to the admin panel
        else:
            error_message = "Invalid Username or Password!"
            return render_template('admin_login.html', error=error_message)  # Reload login page with error

    return render_template('admin_login.html')  # Render the login page initially


@app.route('/admin_panel')
def admin_panel():
    if 'admin' not in session:
        flash("You must be logged in as an admin.", "danger")
        return redirect(url_for('admin'))

    conn = sqlite3.connect("chat.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin.html", users=users)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'admin' not in session:
        flash("You must be logged in as an admin.", "danger")
        return redirect(url_for('admin'))

    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("User deleted successfully.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/update_last_chat/<int:user_id>', methods=['POST'])
@login_required
def update_last_chat(user_id):
    session['last_chat_user_id'] = user_id
    return '', 204

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    # Fetch recent chats for the logged-in user
    cursor.execute('''
        SELECT DISTINCT u.id, u.username, rc.timestamp_local
        FROM recent_chats rc
        JOIN users u ON rc.user_id = u.id
        WHERE rc.sender_id = ?
        ORDER BY rc.timestamp_local DESC
    ''', (current_user.id,))
    recent_chats = cursor.fetchall()

      # Fetch registered users (excluding the current user)
    cursor.execute('SELECT id, username FROM users WHERE id != ?', (current_user.id,))
    users = cursor.fetchall()

    conn.close()

    # Get last opened chat from session or default to first recent chat
    last_chat_user_id = session.get('last_chat_user_id')

    if not last_chat_user_id and recent_chats:
        last_chat_user_id = recent_chats[0][0]  # Default to the most recent chat

    # Update session to remember the last chat user
    session['last_chat_user_id'] = last_chat_user_id

    def get_username(user_id):
        for user in users:
            if user[0] == user_id:
                return user[1]
        return "Unknown"

    return render_template('index.html', users=users, recent_chats=recent_chats, last_chat_user_id=last_chat_user_id,get_username=get_username)

@app.route('/get_recent_chats', methods=['GET'])
@login_required
def get_recent_chats():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.id, u.username, MAX(m.timestamp_utc) as last_message_time
        FROM messages m
        JOIN users u ON (m.sender_id = u.id OR m.recipient_id = u.id)
        WHERE (m.sender_id = ? OR m.recipient_id = ?)
        AND u.id != ?
        GROUP BY u.id, u.username
        ORDER BY last_message_time DESC
    ''', (current_user.id, current_user.id, current_user.id))

    recent_chats = cursor.fetchall()
    conn.close()

    return jsonify(recent_chats)


@socketio.on('chat_cleared')
def handle_chat_cleared(data):
    # Emit to the recipient and sender that the chat was cleared
    emit('chat_cleared', data, room=data['recipient_id'])
    emit('chat_cleared', data, room=data['sender_id'])

@socketio.on('send_message')
def handle_send_message(data):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    timestamp = data.get('timestamp', datetime.utcnow().isoformat())

    cursor.execute(
        '''INSERT INTO messages (sender_id, recipient_id, message, timestamp_utc)
           VALUES (?, ?, ?, ?)''',
        (data['sender_id'], data['recipient_id'], data['message'], timestamp)
    )

    conn.commit()
    conn.close()

    # Emit to both sender and recipient
    emit('receive_message', {**data, 'sender_username': current_user.username}, room=data['recipient_id'])
    emit('receive_message', {**data, 'sender_username': current_user.username}, room=data['sender_id'])

@app.route('/get_messages/<int:recipient_id>', methods=['GET'])
@login_required
def get_messages(recipient_id):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, m.message, m.timestamp_utc
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.recipient_id = ?)
        OR (m.sender_id = ? AND m.recipient_id = ?)
        ORDER BY m.timestamp_utc
    ''', (current_user.id, recipient_id, recipient_id, current_user.id))
    messages = cursor.fetchall()
    conn.close()

    formatted_messages = [(msg[0], msg[1], msg[2]) for msg in messages]
    return jsonify(formatted_messages)


def send_message(recipient_id, message):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    current_time = datetime.utcnow().isoformat()

    # Insert message into messages table
    cursor.execute('''
        INSERT INTO messages (sender_id, recipient_id, message, timestamp_utc)
        VALUES (?, ?, ?, ?)
    ''', (current_user.id, recipient_id, message, current_time))

    # Insert into recent_chats, avoiding duplicates
    cursor.execute('''
        INSERT INTO recent_chats (sender_id, user_id, timestamp_local)
        VALUES (?, ?, ?)
        ON CONFLICT(sender_id, user_id) DO UPDATE SET timestamp_local = excluded.timestamp_local
    ''', (current_user.id, recipient_id, current_time))

    conn.commit()
    conn.close()


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ CLEAR CHAT $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



@app.route('/clear_chat/<int:recipient_id>', methods=['POST'])
@login_required
def clear_chat(recipient_id):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM messages
        WHERE (sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?)
    ''', (current_user.id, recipient_id, recipient_id, current_user.id))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})



@app.route('/api/get_users')
def get_users():
    try:
        conn = sqlite3.connect('chat.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users')
        users = cursor.fetchall()
        conn.close()

        users_data = [{'id': user[0], 'username': user[1]} for user in users]
        return jsonify(users_data)

    except Exception as e:
        print(f"ERROR in get_users: {e}")  # Log error
        return jsonify({"error": str(e)}), 500



@app.template_filter('get_username')
def get_username_filter(user_id):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    username = cursor.fetchone()
    conn.close()
    return username[0] if username else "Unknown"
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$online status$$$$$$$$$$$$$$$$$$$$$$
online_users = set()  # Set to store online user IDs

@socketio.on('connect')
def handle_connect():
    user_id = session.get("user_id")  # Assuming user_id is stored in session
    if user_id:
        online_users.add(user_id)
        emit("user_online", {"user_id": user_id}, broadcast=True)
        print("A user connected")

@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get("user_id")
    if user_id:
        online_users.discard(user_id)
        emit("user_offline", {"user_id": user_id}, broadcast=True)
        print("A user disconnected")

@app.route('/user_status/<int:user_id>')
def get_user_status(user_id):
    return jsonify({"online": user_id in online_users})



#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

@socketio.on("message")
def handle_message(data):
    print("Received message:", data)
    send(data, broadcast=True)  # Broadcast message to all clients

@socketio.on("update_status")
def update_status(data):
    """Update message status dynamically"""
    print(f"Updating message {data['index']} to {data['status']}")
    emit("status_updated", data, broadcast=True)

#900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True)
