from datetime import datetime
import sqlite3
import hashlib
import os
from database.config import API_KEY_SALT

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('database/portfolio.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        ''')

        # API Keys table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Contact Messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE
        )
        ''')

        # Chatbot Messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chatbot_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT NOT NULL,
            message_type TEXT NOT NULL,  -- 'user' or 'bot'
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        self.conn.commit()

    def generate_api_key(self, user_id, name):
        """Generate a unique API key for a user"""
        raw_key = f"{user_id}:{name}:{datetime.now().timestamp()}:{API_KEY_SALT}"
        api_key = hashlib.sha256(raw_key.encode()).hexdigest()
        
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO api_keys (user_id, api_key, name)
        VALUES (?, ?, ?)
        ''', (user_id, api_key, name))
        self.conn.commit()
        return api_key

    def verify_api_key(self, api_key):
        """Verify if an API key is valid"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT user_id, is_active FROM api_keys
        WHERE api_key = ?
        ''', (api_key,))
        result = cursor.fetchone()
        
        if result and result[1]:
            # Update last used timestamp
            cursor.execute('''
            UPDATE api_keys
            SET last_used = CURRENT_TIMESTAMP
            WHERE api_key = ?
            ''', (api_key,))
            self.conn.commit()
            return result[0]  # Return user_id
        return None

    def create_user(self, email, password, first_name, last_name, phone=None):
        """Create a new user"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO users (email, password_hash, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?)
            ''', (email, password_hash, first_name, last_name, phone))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def verify_user(self, email, password):
        """Verify user credentials"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id FROM users
        WHERE email = ? AND password_hash = ? AND is_active = TRUE
        ''', (email, password_hash))
        result = cursor.fetchone()
        
        if result:
            # Update last login
            cursor.execute('''
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (result[0],))
            self.conn.commit()
            return result[0]
        return None

    def store_contact_message(self, first_name, last_name, email, phone, subject, message):
        """Store a contact form message"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO contact_messages (first_name, last_name, email, phone, subject, message)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, phone, subject, message))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_api_keys(self, user_id):
        """Get all API keys for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, api_key, name, created_at, last_used, is_active
        FROM api_keys
        WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchall()

    def deactivate_api_key(self, api_key_id):
        """Deactivate an API key"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE api_keys
        SET is_active = FALSE
        WHERE id = ?
        ''', (api_key_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def store_chatbot_message(self, session_id, message_type, message, user_id=None):
        """Store a chatbot message"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO chatbot_messages (user_id, session_id, message_type, message)
        VALUES (?, ?, ?, ?)
        ''', (user_id, session_id, message_type, message))
        self.conn.commit()
        return cursor.lastrowid

    def get_chatbot_history(self, session_id, limit=50):
        """Get chat history for a session"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, user_id, message_type, message, created_at
        FROM chatbot_messages
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        ''', (session_id, limit))
        return cursor.fetchall()

    def get_user_chatbot_history(self, user_id, limit=50):
        """Get chat history for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, session_id, message_type, message, created_at
        FROM chatbot_messages
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()

    def __del__(self):
        """Close the database connection"""
        if hasattr(self, 'conn'):
            self.conn.close() 