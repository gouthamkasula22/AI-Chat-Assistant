#!/usr/bin/env python3
"""
Simple Database Table Viewer

Quick way to view the contents of database tables in a readable format.
"""

import sqlite3
import os

def view_tables():
    """Display database tables in a simple format"""
    
    if not os.path.exists('chat_history.db'):
        print("❌ Database file not found!")
        return
    
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("📋 CHAT HISTORY DATABASE TABLES")
    print("=" * 60)
    
    try:
        # Show Conversations Table
        print("\n🗂️  CONVERSATIONS TABLE")
        print("-" * 40)
        cursor.execute("SELECT * FROM conversations ORDER BY created_at DESC")
        conversations = cursor.fetchall()
        
        if conversations:
            print(f"{'ID':<3} {'Title':<25} {'Messages':<8} {'Created':<19} {'Session ID'}")
            print("-" * 80)
            for conv in conversations:
                session_short = conv['session_id'][:8] + "..."
                created_short = conv['created_at'][:19]
                title_short = (conv['title'][:22] + "...") if len(conv['title']) > 25 else conv['title']
                print(f"{conv['id']:<3} {title_short:<25} {conv['total_messages']:<8} {created_short:<19} {session_short}")
        else:
            print("No conversations found.")
        
        # Show Messages Table
        print(f"\n💭 MESSAGES TABLE")
        print("-" * 40)
        cursor.execute("""
            SELECT m.id, m.conversation_id, m.role, m.content, m.timestamp, m.response_time
            FROM messages m
            ORDER BY m.timestamp DESC
        """)
        messages = cursor.fetchall()
        
        if messages:
            print(f"{'ID':<3} {'Conv':<4} {'Role':<9} {'Content':<50} {'Time':<19} {'RT'}")
            print("-" * 95)
            for msg in messages:
                content_short = (msg['content'][:47] + "...") if len(msg['content']) > 50 else msg['content']
                timestamp_short = msg['timestamp'][:19] if msg['timestamp'] else "N/A"
                response_time = f"{msg['response_time']:.1f}s" if msg['response_time'] and msg['response_time'] > 0 else "-"
                print(f"{msg['id']:<3} {msg['conversation_id']:<4} {msg['role']:<9} {content_short:<50} {timestamp_short:<19} {response_time}")
        else:
            print("No messages found.")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    view_tables()
