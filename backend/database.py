import sqlite3

DB_NAME = "app_data.sqlite"

def initialize_db():
    """Initialize the database with tables for user sessions, expert selections, and waitlist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # User Sessions Table (Tracking Meeting Limits)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            meeting_count INTEGER DEFAULT 0
        )
    """)

    # Expert Selections Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expert_selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_input TEXT,
            selected_experts TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Waitlist Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            priority_access BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def get_session(session_id):
    """Retrieve the session info, create one if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if the session exists
    cursor.execute("SELECT * FROM user_sessions WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()

    # If session doesn't exist, create a new one
    if not session:
        cursor.execute("INSERT INTO user_sessions (session_id, meeting_count) VALUES (?, ?)", (session_id, 0))
        conn.commit()
        session = (session_id, 0)  # Default values

    conn.close()
    return session  # Returns tuple (session_id, meeting_count)

def update_meeting_count(session_id):
    """Increment the meeting count for a given session."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("UPDATE user_sessions SET meeting_count = meeting_count + 1 WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def save_expert_selection(session_id, user_input, experts_selected):
    """Save expert selection to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expert_selections (session_id, user_input, selected_experts)
        VALUES (?, ?, ?)
    """, (session_id, user_input, ", ".join(experts_selected)))
    conn.commit()
    conn.close()

def save_waitlist(email: str, priority_access: bool = False):
    """Save a new waitlist entry with the user's email and priority access flag."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO waitlist (email, priority_access) VALUES (?, ?)", (email, int(priority_access)))
        conn.commit()
    except Exception as e:
        print("Error saving waitlist entry:", e)
    finally:
        conn.close()