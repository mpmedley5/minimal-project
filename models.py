"""
Database Models for CompTIA Domain Knowledge Chatbot

This module defines SQLAlchemy models for the application's core entities:
- User: User accounts with authentication details
- ChatSession: Chat sessions scoped to domains
- Message: Individual messages within chat sessions

These models replace the previous JSON-based storage with a relational database
for better scalability, data integrity, and query performance.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy instance
db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and user management."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True)  # UUID as string
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationship to chat sessions
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'

class ChatSession(db.Model):
    """Chat session model for domain-scoped conversations."""
    __tablename__ = 'chat_sessions'

    id = db.Column(db.String(36), primary_key=True)  # UUID as string
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    domain_id = db.Column(db.String(100), nullable=False)
    chat_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to messages
    messages = db.relationship('Message', backref='chat_session', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ChatSession {self.chat_name}>'

class Message(db.Model):
    """Message model for individual chat messages."""
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True)  # UUID as string
    chat_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Message {self.role}: {self.content[:50]}...>'