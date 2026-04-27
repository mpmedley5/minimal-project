#!/usr/bin/env python3
"""
Database Viewer for CompTIA Domain Knowledge Chatbot

This script displays the contents of the SQLite database in a readable format.
Run this script to view all users, chat sessions, and messages.
"""

import os
import sys
from datetime import datetime

# Add current directory to path so we can import our models
sys.path.insert(0, os.path.dirname(__file__))

from models import db, User, ChatSession, Message
from web_app import app

def display_database_contents():
    """Display all data from the database in a readable format."""

    with app.app_context():
        print("=" * 80)
        print("📊 COMPTIA DOMAIN KNOWLEDGE CHATBOT DATABASE CONTENTS")
        print("=" * 80)

        # Display Users
        print("\n👥 USERS:")
        print("-" * 40)
        users = User.query.all()
        if not users:
            print("No users found.")
        else:
            for user in users:
                print(f"ID: {user.id}")
                print(f"Name: {user.first_name} {user.last_name}")
                print(f"Email: {user.email}")
                print(f"Created: {user.created_at}")
                print(f"Last Login: {user.last_login}")
                print(f"Chat Sessions: {len(user.chat_sessions)}")
                print("-" * 20)

        # Display Chat Sessions
        print("\n💬 CHAT SESSIONS:")
        print("-" * 40)
        chats = ChatSession.query.all()
        if not chats:
            print("No chat sessions found.")
        else:
            for chat in chats:
                print(f"ID: {chat.id}")
                print(f"User ID: {chat.user_id}")
                print(f"Domain: {chat.domain_id}")
                print(f"Chat Name: {chat.chat_name}")
                print(f"Created: {chat.created_at}")
                print(f"Last Updated: {chat.last_updated}")
                print(f"Messages: {len(chat.messages)}")
                print("-" * 20)

        # Display Messages
        print("\n📝 MESSAGES:")
        print("-" * 40)
        messages = Message.query.order_by(Message.timestamp).all()
        if not messages:
            print("No messages found.")
        else:
            for msg in messages:
                print(f"ID: {msg.id}")
                print(f"Chat ID: {msg.chat_id}")
                print(f"Role: {msg.role}")
                print(f"Timestamp: {msg.timestamp}")
                print(f"Content: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
                print("-" * 20)

        print("\n" + "=" * 80)
        print(f"📈 SUMMARY: {len(users)} users, {len(chats)} chat sessions, {len(messages)} messages")
        print("=" * 80)

if __name__ == "__main__":
    display_database_contents()