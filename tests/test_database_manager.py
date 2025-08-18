import unittest
import sqlite3
import tempfile
import os

from database.db_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        self.db_manager = DatabaseManager(self.db_path)

    def tearDown(self):
        """Clean up test database"""
        # Close any open connections
        if hasattr(self.db_manager, '_connection_pool'):
            for conn in self.db_manager._connection_pool:
                conn.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_database_initialization(self):
        """Test that database schema is created correctly"""
        # Check if tables exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        self.assertIn('conversations', tables)
        self.assertIn('messages', tables)
        conn.close()

    def test_create_conversation(self):
        """Test conversation creation"""
        title = "Test Conversation"
        conversation_id = self.db_manager.create_conversation(title)

        self.assertIsNotNone(conversation_id)
        self.assertIsInstance(conversation_id, int)

    def test_add_message(self):
        """Test adding messages to conversation"""
        # Create conversation first
        conversation_id = self.db_manager.create_conversation("Test Chat")

        # Add user message
        user_msg_id = self.db_manager.add_message(
            conversation_id, "user", "Hello AI", "Gemini Pro"
        )
        self.assertIsNotNone(user_msg_id)

        # Add AI response
        ai_msg_id = self.db_manager.add_message(
            conversation_id, "assistant", "Hello! How can I help?", "Gemini Pro"
        )
        self.assertIsNotNone(ai_msg_id)

    def test_get_conversation_messages(self):
        """Test retrieving conversation messages"""
        conversation_id = self.db_manager.create_conversation("Test Chat")

        # Add some messages
        self.db_manager.add_message(conversation_id, "user", "Hello", "Gemini Pro")
        self.db_manager.add_message(conversation_id, "assistant", "Hi there!", "Gemini Pro")

        messages = self.db_manager.get_conversation_messages(conversation_id)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'user')
        self.assertEqual(messages[1]['role'], 'assistant')

    def test_get_recent_conversations(self):
        """Test retrieving recent conversations"""
        # Create multiple conversations
        conv1 = self.db_manager.create_conversation("Chat 1")
        conv2 = self.db_manager.create_conversation("Chat 2")

        recent = self.db_manager.get_recent_conversations(limit=10)

        self.assertEqual(len(recent), 2)
        # Should be ordered by most recent first
        conversation_ids = [conv['id'] for conv in recent]
        self.assertIn(conv1, conversation_ids)
        self.assertIn(conv2, conversation_ids)

    def test_delete_conversation(self):
        """Test conversation deletion"""
        conversation_id = self.db_manager.create_conversation("To Delete")
        self.db_manager.add_message(conversation_id, "user", "Test", "Gemini Pro")

        # Delete conversation
        success = self.db_manager.delete_conversation(conversation_id)
        self.assertTrue(success)

        # Verify it's gone
        messages = self.db_manager.get_conversation_messages(conversation_id)
        self.assertEqual(len(messages), 0)

    def test_conversation_exists(self):
        """Test checking if conversation exists"""
        conversation_id = self.db_manager.create_conversation("Test Chat")

        # Check that it exists
        recent = self.db_manager.get_recent_conversations(limit=10)
        conversation_ids = [conv['id'] for conv in recent]
        self.assertIn(conversation_id, conversation_ids)

        # Check that non-existent ID doesn't exist
        non_existent_messages = self.db_manager.get_conversation_messages(99999)
        self.assertEqual(len(non_existent_messages), 0)


if __name__ == '__main__':
    unittest.main()
