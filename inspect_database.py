#!/usr/bin/env python3
"""
Database Inspector for Chat History Management

This script provides a comprehensive view of the chat_history.db database,
showing schema, data, and relationships.
"""

import sqlite3
import os
from datetime import datetime

def format_timestamp(timestamp_str):
    """Format timestamp for better readability"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def inspect_database():
    """Comprehensive database inspection"""
    
    if not os.path.exists('chat_history.db'):
        print("❌ Database file 'chat_history.db' not found!")
        return
    
    print("🔍 CHAT HISTORY DATABASE INSPECTOR")
    print("=" * 50)
    
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    cursor = conn.cursor()
    
    try:
        # 1. Database Information
        print("\n📊 DATABASE OVERVIEW")
        print("-" * 30)
        
        file_size = os.path.getsize('chat_history.db')
        print(f"File Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # 2. Tables and Schema
        print("\n🏗️  DATABASE SCHEMA")
        print("-" * 30)
        
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table['name']
            table_sql = table['sql']
            
            print(f"\n📋 Table: {table_name}")
            print("Schema:")
            # Format the SQL for better readability
            formatted_sql = table_sql.replace('(', '(\n    ').replace(',', ',\n    ').replace(')', '\n)')
            print(formatted_sql)
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("\nColumns:")
            for col in columns:
                pk_indicator = " (PRIMARY KEY)" if col[5] else ""
                not_null = " NOT NULL" if col[3] else ""
                default_val = f" DEFAULT {col[4]}" if col[4] else ""
                print(f"  • {col[1]} ({col[2]}){pk_indicator}{not_null}{default_val}")
        
        # 3. Indexes
        print(f"\n🔗 INDEXES")
        print("-" * 30)
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = cursor.fetchall()
        
        if indexes:
            for idx in indexes:
                print(f"• {idx['name']}")
                print(f"  {idx['sql']}")
        else:
            print("No custom indexes found")
        
        # 4. Data Summary
        print(f"\n📈 DATA SUMMARY")
        print("-" * 30)
        
        # Conversations count
        cursor.execute("SELECT COUNT(*) as count FROM conversations")
        conv_count = cursor.fetchone()['count']
        print(f"Total Conversations: {conv_count}")
        
        # Messages count
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        msg_count = cursor.fetchone()['count']
        print(f"Total Messages: {msg_count}")
        
        # Messages per conversation
        if conv_count > 0:
            cursor.execute("""
                SELECT 
                    AVG(total_messages) as avg_messages,
                    MIN(total_messages) as min_messages,
                    MAX(total_messages) as max_messages
                FROM conversations
            """)
            stats = cursor.fetchone()
            print(f"Average Messages per Conversation: {stats['avg_messages']:.1f}")
            print(f"Range: {stats['min_messages']} - {stats['max_messages']} messages")
        
        # 5. Conversations Table Data
        if conv_count > 0:
            print(f"\n💬 CONVERSATIONS TABLE")
            print("-" * 30)
            
            cursor.execute("""
                SELECT id, title, created_at, updated_at, ai_model, total_messages, session_id
                FROM conversations 
                ORDER BY created_at DESC
            """)
            conversations = cursor.fetchall()
            
            for conv in conversations:
                print(f"\n🗂️  Conversation ID: {conv['id']}")
                print(f"   Title: \"{conv['title']}\"")
                print(f"   Created: {format_timestamp(conv['created_at'])}")
                print(f"   Updated: {format_timestamp(conv['updated_at'])}")
                print(f"   AI Model: {conv['ai_model']}")
                print(f"   Total Messages: {conv['total_messages']}")
                print(f"   Session ID: {conv['session_id'][:16]}...")
        
        # 6. Recent Messages
        if msg_count > 0:
            print(f"\n💭 RECENT MESSAGES")
            print("-" * 30)
            
            cursor.execute("""
                SELECT m.id, m.conversation_id, m.role, m.content, m.timestamp, m.response_time,
                       c.title as conv_title
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                ORDER BY m.timestamp DESC
                LIMIT 5
            """)
            messages = cursor.fetchall()
            
            for msg in messages:
                role_emoji = "👤" if msg['role'] == 'user' else "🤖"
                content_preview = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                
                print(f"\n{role_emoji} {msg['role'].upper()} (ID: {msg['id']})")
                print(f"   Conversation: \"{msg['conv_title']}\" (ID: {msg['conversation_id']})")
                print(f"   Content: \"{content_preview}\"")
                print(f"   Timestamp: {format_timestamp(msg['timestamp'])}")
                if msg['response_time'] and msg['response_time'] > 0:
                    print(f"   Response Time: {msg['response_time']:.2f}s")
        
        # 7. Relationship Verification
        print(f"\n🔗 RELATIONSHIP VERIFICATION")
        print("-" * 30)
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT m.conversation_id) as conversations_with_messages,
                COUNT(DISTINCT c.id) as total_conversations
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
        """)
        rel_check = cursor.fetchone()
        
        print(f"Conversations with messages: {rel_check['conversations_with_messages']}")
        print(f"Total conversations: {rel_check['total_conversations']}")
        
        # Check for orphaned messages
        cursor.execute("""
            SELECT COUNT(*) as orphaned_messages
            FROM messages m
            LEFT JOIN conversations c ON m.conversation_id = c.id
            WHERE c.id IS NULL
        """)
        orphaned = cursor.fetchone()['orphaned_messages']
        
        if orphaned > 0:
            print(f"⚠️  Orphaned messages (no parent conversation): {orphaned}")
        else:
            print("✅ No orphaned messages found")
        
        # 8. Response Time Statistics
        if msg_count > 0:
            cursor.execute("""
                SELECT 
                    COUNT(*) as ai_messages,
                    AVG(response_time) as avg_response_time,
                    MIN(response_time) as min_response_time,
                    MAX(response_time) as max_response_time
                FROM messages 
                WHERE role = 'assistant' AND response_time > 0
            """)
            response_stats = cursor.fetchone()
            
            if response_stats['ai_messages'] > 0:
                print(f"\n⏱️  RESPONSE TIME STATISTICS")
                print("-" * 30)
                print(f"AI Messages with timing: {response_stats['ai_messages']}")
                print(f"Average Response Time: {response_stats['avg_response_time']:.2f}s")
                print(f"Fastest Response: {response_stats['min_response_time']:.2f}s")
                print(f"Slowest Response: {response_stats['max_response_time']:.2f}s")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        conn.close()
    
    print(f"\n✅ Database inspection complete!")
    print("=" * 50)

if __name__ == "__main__":
    inspect_database()
