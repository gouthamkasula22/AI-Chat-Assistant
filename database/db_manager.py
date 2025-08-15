"""
Database Manager for Chat History Management

This module handles all database operations for storing and retrieving chat conversations.
It uses SQLite for persistence and follows proper database design patterns.

Key Features:
- Normalized schema with conversations and messages tables
- Automatic database initialization and migrations
- Proper error handling and logging
- Type hints for all functions
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database operations for chat history storage.
    
    This class implements a singleton-like pattern where each instance
    manages its own database connection and provides methods for:
    - Creating and managing conversations
    - Storing and retrieving messages
    - Database migrations and schema updates
    """
    
    def __init__(self, db_path: str = "chat_history.db"):
        """
        Initialize the database manager with a specified database path.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()
        logger.info(f"Database manager initialized with database: {db_path}")
    
    def _initialize_database(self) -> None:
        """
        Create the database schema if it doesn't exist.
        
        This method creates two main tables:
        1. conversations: Stores conversation metadata
        2. messages: Stores individual messages within conversations
        
        The schema follows database normalization principles:
        - Primary keys for unique identification
        - Foreign key relationship between messages and conversations
        - Proper data types and constraints
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create conversations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ai_model TEXT DEFAULT 'gemini-pro',
                        total_messages INTEGER DEFAULT 0,
                        session_id TEXT UNIQUE
                    )
                """)
                
                # Create messages table with foreign key relationship
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id INTEGER NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        response_time REAL DEFAULT 0.0,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                    ON messages(conversation_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
                    ON conversations(session_id)
                """)
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        This ensures proper connection handling:
        - Automatic connection closing
        - Error handling
        - Transaction management
        
        Yields:
            sqlite3.Connection: Database connection object
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            # Set row factory to return dict-like objects
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def create_conversation(self, session_id: str, title: str = "New Chat", 
                          ai_model: str = "gemini-pro") -> int:
        """
        Create a new conversation record.
        
        Args:
            session_id (str): Unique session identifier
            title (str): Human-readable conversation title
            ai_model (str): AI model used for this conversation
            
        Returns:
            int: The ID of the newly created conversation
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (session_id, title, ai_model)
                    VALUES (?, ?, ?)
                """, (session_id, title, ai_model))
                
                conversation_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created conversation {conversation_id} for session {session_id}")
                return conversation_id
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning(f"Conversation already exists for session {session_id}")
                return self.get_conversation_by_session(session_id)['id']
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    def get_conversation_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a conversation by its session ID.
        
        Args:
            session_id (str): Session identifier to search for
            
        Returns:
            Optional[Dict[str, Any]]: Conversation data or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, created_at, updated_at, ai_model, 
                           total_messages, session_id
                    FROM conversations 
                    WHERE session_id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve conversation: {e}")
            return None
    
    def add_message(self, conversation_id: int, role: str, content: str, 
                   response_time: float = 0.0) -> int:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id (int): ID of the conversation
            role (str): Message role ('user' or 'assistant')
            content (str): Message content
            response_time (float): Time taken to generate response (for assistant messages)
            
        Returns:
            int: ID of the newly created message
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert the message
                cursor.execute("""
                    INSERT INTO messages (conversation_id, role, content, response_time)
                    VALUES (?, ?, ?, ?)
                """, (conversation_id, role, content, response_time))
                
                message_id = cursor.lastrowid
                
                # Update conversation's message count and last updated time
                cursor.execute("""
                    UPDATE conversations 
                    SET total_messages = total_messages + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (conversation_id,))
                
                conn.commit()
                logger.info(f"Added {role} message to conversation {conversation_id}")
                return message_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add message: {e}")
            raise
    
    def get_conversation_messages(self, conversation_id: int, 
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all messages for a conversation.
        
        Args:
            conversation_id (int): ID of the conversation
            limit (Optional[int]): Maximum number of messages to return
            
        Returns:
            List[Dict[str, Any]]: List of message dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, role, content, timestamp, response_time
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, (conversation_id,))
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve messages: {e}")
            return []
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent conversations.
        
        Args:
            limit (int): Maximum number of conversations to return
            
        Returns:
            List[Dict[str, Any]]: List of conversation dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, created_at, updated_at, ai_model, 
                           total_messages, session_id
                    FROM conversations 
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve recent conversations: {e}")
            return []
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id (int): ID of conversation to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Deleted conversation {conversation_id}")
                    return True
                
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get database statistics for monitoring and debugging.
        
        Returns:
            Dict[str, int]: Statistics about conversations and messages
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Count conversations
                cursor.execute("SELECT COUNT(*) FROM conversations")
                conversation_count = cursor.fetchone()[0]
                
                # Count messages
                cursor.execute("SELECT COUNT(*) FROM messages")
                message_count = cursor.fetchone()[0]
                
                # Get database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'conversations': conversation_count,
                    'messages': message_count,
                    'db_size_bytes': db_size
                }
                
        except (sqlite3.Error, OSError) as e:
            logger.error(f"Failed to get database stats: {e}")
            return {'conversations': 0, 'messages': 0, 'db_size_bytes': 0}
