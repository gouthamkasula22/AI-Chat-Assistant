#!/usr/bin/env python3
"""
Interactive Database Explorer

Choose different aspects of your chat history database to explore.
"""

import sqlite3
import os
from datetime import datetime
import json

def format_timestamp(timestamp_str):
    """Format timestamp for better readability"""
    try:
        if timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        pass
    return timestamp_str or "N/A"

def show_schema():
    """Show detailed database schema"""
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n🏗️  DATABASE SCHEMA ANALYSIS")
    print("=" * 50)
    
    # Get all tables
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    for table in tables:
        if table['name'] == 'sqlite_sequence':
            continue
            
        print(f"\n📋 Table: {table['name']}")
        print("-" * 30)
        
        # Get column information
        cursor.execute(f"PRAGMA table_info({table['name']})")
        columns = cursor.fetchall()
        
        print("Columns:")
        for col in columns:
            pk = " (PRIMARY KEY)" if col[5] else ""
            not_null = " NOT NULL" if col[3] else ""
            default = f" DEFAULT {col[4]}" if col[4] else ""
            print(f"  • {col[1]} - {col[2]}{pk}{not_null}{default}")
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table['name']})")
        fks = cursor.fetchall()
        
        if fks:
            print("Foreign Keys:")
            for fk in fks:
                print(f"  • {fk[3]} → {fk[2]}.{fk[4]} (ON DELETE {fk[6]})")
        
        # Get indexes
        cursor.execute(f"PRAGMA index_list({table['name']})")
        indexes = cursor.fetchall()
        
        if indexes:
            print("Indexes:")
            for idx in indexes:
                if not idx[1].startswith('sqlite_'):  # Skip auto-created indexes
                    print(f"  • {idx[1]} ({'UNIQUE' if idx[2] else 'NON-UNIQUE'})")
    
    conn.close()

def show_conversations():
    """Show detailed conversation analysis"""
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n💬 CONVERSATION ANALYSIS")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) as count FROM conversations")
    total = cursor.fetchone()['count']
    print(f"Total Conversations: {total}")
    
    if total == 0:
        print("No conversations found.")
        conn.close()
        return
    
    # Detailed conversation info
    cursor.execute("""
        SELECT id, title, created_at, updated_at, ai_model, total_messages, session_id,
               datetime(created_at) as created_date,
               datetime(updated_at) as updated_date
        FROM conversations 
        ORDER BY created_at DESC
    """)
    conversations = cursor.fetchall()
    
    for i, conv in enumerate(conversations, 1):
        print(f"\n🗂️  Conversation {i} (ID: {conv['id']})")
        print(f"   📝 Title: \"{conv['title']}\"")
        print(f"   🤖 AI Model: {conv['ai_model']}")
        print(f"   💬 Messages: {conv['total_messages']}")
        print(f"   📅 Created: {format_timestamp(conv['created_at'])}")
        print(f"   🔄 Updated: {format_timestamp(conv['updated_at'])}")
        print(f"   🔑 Session: {conv['session_id'][:16]}...")
        
        # Duration calculation
        try:
            created = datetime.fromisoformat(conv['created_at'])
            updated = datetime.fromisoformat(conv['updated_at'])
            duration = updated - created
            print(f"   ⏱️  Duration: {duration}")
        except:
            pass
    
    conn.close()

def show_messages():
    """Show detailed message analysis"""
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n💭 MESSAGE ANALYSIS")
    print("=" * 50)
    
    # Message statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_messages,
            COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
            COUNT(CASE WHEN role = 'assistant' THEN 1 END) as ai_messages,
            AVG(LENGTH(content)) as avg_length,
            MAX(LENGTH(content)) as max_length,
            MIN(LENGTH(content)) as min_length
        FROM messages
    """)
    stats = cursor.fetchone()
    
    print(f"📊 Message Statistics:")
    print(f"   Total Messages: {stats['total_messages']}")
    print(f"   User Messages: {stats['user_messages']}")
    print(f"   AI Messages: {stats['ai_messages']}")
    print(f"   Average Length: {stats['avg_length']:.1f} characters")
    print(f"   Length Range: {stats['min_length']} - {stats['max_length']} characters")
    
    # Recent messages
    print(f"\n📨 Recent Messages:")
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
        content_preview = (msg['content'][:60] + "...") if len(msg['content']) > 60 else msg['content']
        
        print(f"\n{role_emoji} Message {msg['id']} ({msg['role']})")
        print(f"   📝 Content: \"{content_preview}\"")
        print(f"   🗂️  From: \"{msg['conv_title']}\" (Conv {msg['conversation_id']})")
        print(f"   📅 Time: {format_timestamp(msg['timestamp'])}")
        if msg['response_time'] and msg['response_time'] > 0:
            print(f"   ⏱️  Response Time: {msg['response_time']:.2f}s")
    
    conn.close()

def show_performance():
    """Show performance and response time analysis"""
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n⚡ PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    # Response time statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as ai_responses,
            AVG(response_time) as avg_time,
            MIN(response_time) as min_time,
            MAX(response_time) as max_time,
            SUM(response_time) as total_time
        FROM messages 
        WHERE role = 'assistant' AND response_time > 0
    """)
    stats = cursor.fetchone()
    
    if stats['ai_responses'] > 0:
        print(f"🤖 AI Response Statistics:")
        print(f"   Total AI Responses: {stats['ai_responses']}")
        print(f"   Average Response Time: {stats['avg_time']:.2f} seconds")
        print(f"   Fastest Response: {stats['min_time']:.2f} seconds")
        print(f"   Slowest Response: {stats['max_time']:.2f} seconds")
        print(f"   Total AI Processing Time: {stats['total_time']:.2f} seconds")
        
        # Performance by conversation
        print(f"\n📈 Performance by Conversation:")
        cursor.execute("""
            SELECT c.id, c.title, 
                   COUNT(m.id) as ai_messages,
                   AVG(m.response_time) as avg_response_time,
                   MIN(m.response_time) as fastest,
                   MAX(m.response_time) as slowest
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE m.role = 'assistant' AND m.response_time > 0
            GROUP BY c.id, c.title
            ORDER BY avg_response_time DESC
        """)
        conv_perf = cursor.fetchall()
        
        for conv in conv_perf:
            title_short = (conv['title'][:30] + "...") if len(conv['title']) > 30 else conv['title']
            print(f"   🗂️  \"{title_short}\":")
            print(f"      Messages: {conv['ai_messages']}, Avg: {conv['avg_response_time']:.2f}s")
            print(f"      Range: {conv['fastest']:.2f}s - {conv['slowest']:.2f}s")
    else:
        print("No response time data available.")
    
    conn.close()

def show_storage():
    """Show storage and file information"""
    print("\n💾 STORAGE ANALYSIS")
    print("=" * 50)
    
    if not os.path.exists('chat_history.db'):
        print("Database file not found.")
        return
    
    # File information
    file_size = os.path.getsize('chat_history.db')
    file_kb = file_size / 1024
    file_mb = file_kb / 1024
    
    print(f"📁 Database File:")
    print(f"   Path: chat_history.db")
    print(f"   Size: {file_size:,} bytes")
    print(f"   Size: {file_kb:.1f} KB")
    if file_mb >= 1:
        print(f"   Size: {file_mb:.2f} MB")
    
    # Page information
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]
    
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    
    print(f"\n📄 Database Pages:")
    print(f"   Page Count: {page_count}")
    print(f"   Page Size: {page_size} bytes")
    print(f"   Total Pages Size: {page_count * page_size:,} bytes")
    
    # Table sizes (approximate)
    print(f"\n📊 Estimated Table Sizes:")
    tables = ['conversations', 'messages']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        # Rough estimation of space per row
        avg_row_size = 0
        if table == 'conversations':
            avg_row_size = 200  # Rough estimate
        elif table == 'messages':
            cursor.execute("SELECT AVG(LENGTH(content)) FROM messages")
            avg_content = cursor.fetchone()[0] or 0
            avg_row_size = avg_content + 100  # Content + metadata
        
        estimated_size = row_count * avg_row_size
        print(f"   {table}: {row_count} rows (~{estimated_size:,.0f} bytes)")
    
    conn.close()

def show_integrity():
    """Show data integrity and relationship analysis"""
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n🔗 DATA INTEGRITY ANALYSIS")
    print("=" * 50)
    
    # Check foreign key integrity
    print("🔍 Foreign Key Checks:")
    
    # Check for orphaned messages
    cursor.execute("""
        SELECT COUNT(*) as orphaned
        FROM messages m
        LEFT JOIN conversations c ON m.conversation_id = c.id
        WHERE c.id IS NULL
    """)
    orphaned = cursor.fetchone()['orphaned']
    
    if orphaned > 0:
        print(f"   ⚠️  Orphaned messages: {orphaned}")
    else:
        print(f"   ✅ No orphaned messages")
    
    # Check message count consistency
    cursor.execute("""
        SELECT c.id, c.title, c.total_messages,
               COUNT(m.id) as actual_messages,
               (c.total_messages - COUNT(m.id)) as difference
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        GROUP BY c.id, c.title, c.total_messages
        HAVING difference != 0
    """)
    inconsistent = cursor.fetchall()
    
    if inconsistent:
        print(f"   ⚠️  Message count inconsistencies found:")
        for conv in inconsistent:
            print(f"      Conv {conv['id']}: Recorded={conv['total_messages']}, Actual={conv['actual_messages']}")
    else:
        print(f"   ✅ Message counts consistent")
    
    # Check for invalid roles
    cursor.execute("""
        SELECT COUNT(*) as invalid_roles
        FROM messages
        WHERE role NOT IN ('user', 'assistant')
    """)
    invalid_roles = cursor.fetchone()['invalid_roles']
    
    if invalid_roles > 0:
        print(f"   ⚠️  Invalid message roles: {invalid_roles}")
    else:
        print(f"   ✅ All message roles valid")
    
    # Check for null or empty content
    cursor.execute("""
        SELECT COUNT(*) as empty_content
        FROM messages
        WHERE content IS NULL OR content = ''
    """)
    empty_content = cursor.fetchone()['empty_content']
    
    if empty_content > 0:
        print(f"   ⚠️  Empty message content: {empty_content}")
    else:
        print(f"   ✅ All messages have content")
    
    conn.close()

def show_export():
    """Export data in different formats"""
    print("\n📤 DATA EXPORT OPTIONS")
    print("=" * 50)
    
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Choose export format:")
    print("1. JSON export")
    print("2. CSV-like text export")
    print("3. Raw SQL dump")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # JSON export
        print("\n📄 JSON Export:")
        
        cursor.execute("""
            SELECT c.*, 
                   GROUP_CONCAT(
                       json_object(
                           'id', m.id,
                           'role', m.role,
                           'content', m.content,
                           'timestamp', m.timestamp,
                           'response_time', m.response_time
                       )
                   ) as messages_json
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
        """)
        
        for conv in cursor.fetchall():
            conv_data = {
                'id': conv['id'],
                'title': conv['title'],
                'created_at': conv['created_at'],
                'updated_at': conv['updated_at'],
                'ai_model': conv['ai_model'],
                'total_messages': conv['total_messages'],
                'session_id': conv['session_id']
            }
            print(json.dumps(conv_data, indent=2))
            print()
    
    elif choice == "2":
        # CSV-like export
        print("\n📊 CSV Export:")
        print("ID,Type,ConvID,Title,Role,Content,Timestamp,ResponseTime")
        
        cursor.execute("""
            SELECT 'CONV' as type, c.id, c.id as conv_id, c.title, '' as role, 
                   c.title as content, c.created_at, 0 as response_time
            FROM conversations c
            UNION ALL
            SELECT 'MSG' as type, m.id, m.conversation_id, c.title, m.role,
                   m.content, m.timestamp, m.response_time
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            ORDER BY conv_id, type DESC, timestamp
        """)
        
        for row in cursor.fetchall():
            print(f"{row[1]},{row[0]},{row[2]},\"{row[3]}\",{row[4]},\"{row[5]}\",{row[6]},{row[7]}")
    
    elif choice == "3":
        # SQL dump
        print("\n💾 SQL Dump:")
        print("-- Conversations")
        cursor.execute("SELECT * FROM conversations")
        for conv in cursor.fetchall():
            values = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in conv])
            print(f"INSERT INTO conversations VALUES ({values});")
        
        print("\n-- Messages")
        cursor.execute("SELECT * FROM messages")
        for msg in cursor.fetchall():
            values = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in msg])
            print(f"INSERT INTO messages VALUES ({values});")
    
    conn.close()

def main():
    """Main interactive menu"""
    
    if not os.path.exists('chat_history.db'):
        print("❌ Database file 'chat_history.db' not found!")
        print("Make sure you're in the correct directory and have used the chat app.")
        return
    
    while True:
        print("\n🔍 DATABASE EXPLORER")
        print("=" * 40)
        print("Choose what to explore:")
        print()
        print("1. 🏗️  Schema & Structure")
        print("2. 💬 Conversations")
        print("3. 💭 Messages")  
        print("4. ⚡ Performance & Response Times")
        print("5. 💾 Storage & File Info")
        print("6. 🔗 Data Integrity")
        print("7. 📤 Export Data")
        print("8. 🚪 Exit")
        print()
        
        choice = input("Enter your choice (1-8): ").strip()
        
        if choice == "1":
            show_schema()
        elif choice == "2":
            show_conversations()
        elif choice == "3":
            show_messages()
        elif choice == "4":
            show_performance()
        elif choice == "5":
            show_storage()
        elif choice == "6":
            show_integrity()
        elif choice == "7":
            show_export()
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
