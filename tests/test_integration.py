import unittest
import tempfile
import os
from unittest.mock import Mock

# Integration test for core functionality
from database.db_manager import DatabaseManager
from services.chat_history_service import ChatHistoryService


class TestBasicIntegration(unittest.TestCase):
    def setUp(self):
        """Set up integration test environment"""
        # Create temporary database
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name

        # Initialize components
        self.db_manager = DatabaseManager(self.db_path)
        self.chat_service = ChatHistoryService(self.db_path)

    def tearDown(self):
        """Clean up test environment"""
        # Close any open connections
        if hasattr(self.db_manager, '_connection_pool'):
            for conn in self.db_manager._connection_pool:
                conn.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_complete_conversation_flow(self):
        """Test a complete conversation flow from start to finish"""

        # 1. Start new conversation using correct method
        conversation = self.chat_service.start_or_resume_conversation("integration-test-session", "TestModel")
        self.assertIsNotNone(conversation)
        self.assertIn('id', conversation)  # Actual field name is 'id'
        conversation_id = conversation['id']

        # 2. Add user message using correct method signature
        user_msg = self.chat_service.add_user_message("integration-test-session", "Hello AI!")
        self.assertIsNotNone(user_msg)
        self.assertIn('id', user_msg)  # Actual field name is 'id'

        # 3. Add AI response using correct method signature
        ai_response = "Hello! How can I help you today?"
        ai_msg = self.chat_service.add_assistant_message("integration-test-session", ai_response, 0.5)
        self.assertIsNotNone(ai_msg)
        self.assertIn('id', ai_msg)  # Actual field name is 'id'

        # 4. Retrieve conversation history using session_id
        history = self.chat_service.get_conversation_history("integration-test-session")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['role'], 'user')
        self.assertEqual(history[0]['content'], 'Hello AI!')
        self.assertEqual(history[1]['role'], 'assistant')
        self.assertEqual(history[1]['content'], ai_response)

        # 5. Check recent conversations
        recent = self.chat_service.get_recent_conversations(5)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]['id'], conversation_id)

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation"""

        conversation = self.chat_service.start_or_resume_conversation("multi-turn-session", "TestModel")
        conversation_id = conversation['id']  # Use correct field name
        session_id = "multi-turn-session"

        # Turn 1 - use session_id, not conversation_id
        self.chat_service.add_user_message(session_id, "What's 2+2?")
        self.chat_service.add_assistant_message(session_id, "2+2 equals 4", 0.3)

        # Turn 2
        self.chat_service.add_user_message(session_id, "What about 3+3?")
        self.chat_service.add_assistant_message(session_id, "3+3 equals 6", 0.4)

        # Verify conversation has 4 messages (2 user, 2 assistant) - use session_id
        final_history = self.chat_service.get_conversation_history(session_id)
        self.assertEqual(len(final_history), 4)

        # Check message order
        self.assertEqual(final_history[0]['role'], 'user')
        self.assertEqual(final_history[1]['role'], 'assistant')
        self.assertEqual(final_history[2]['role'], 'user')
        self.assertEqual(final_history[3]['role'], 'assistant')

    def test_multiple_conversations(self):
        """Test managing multiple conversations"""

        # Create multiple conversations
        conv1 = self.chat_service.start_or_resume_conversation("math-session", "TestModel")
        conv2 = self.chat_service.start_or_resume_conversation("programming-session", "TestModel")
        conv3 = self.chat_service.start_or_resume_conversation("general-session", "TestModel")

        # Add messages to each using session_id and correct method signature
        self.chat_service.add_user_message("math-session", "What's calculus?")
        self.chat_service.add_user_message("programming-session", "How do I code in Python?")
        self.chat_service.add_user_message("general-session", "Hello there!")

        # Check that all conversations exist
        recent = self.chat_service.get_recent_conversations(10)
        self.assertEqual(len(recent), 3)

        # Check that each conversation has the right content using session_id
        conv1_history = self.chat_service.get_conversation_history("math-session")
        conv2_history = self.chat_service.get_conversation_history("programming-session")
        conv3_history = self.chat_service.get_conversation_history("general-session")

        self.assertIn("calculus", conv1_history[0]['content'])
        self.assertIn("Python", conv2_history[0]['content'])
        self.assertIn("Hello", conv3_history[0]['content'])

    def test_conversation_persistence(self):
        """Test that conversations persist across service restarts"""

        # Create conversation and add messages
        conversation = self.chat_service.start_or_resume_conversation("persistence-session", "TestModel")
        conversation_id = conversation['id']  # Use correct field name
        session_id = "persistence-session"

        # Add messages using session_id and correct method signatures
        self.chat_service.add_user_message(session_id, "Test message")
        self.chat_service.add_assistant_message(session_id, "Test response", 0.2)

        # Create new chat service instance (simulating restart) using same DB path
        new_chat_service = ChatHistoryService(self.db_path)

        # Check that conversation still exists using session_id
        history = new_chat_service.get_conversation_history(session_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['content'], "Test message")
        self.assertEqual(history[1]['content'], "Test response")

    def test_error_handling(self):
        """Test basic error handling"""

        # Test getting messages from non-existent conversation using session_id
        non_existent_history = self.chat_service.get_conversation_history("non-existent-session")
        self.assertEqual(len(non_existent_history), 0)

        # Test that we can still create new conversations after errors
        conversation = self.chat_service.start_or_resume_conversation("error-test-session", "TestModel")
        conversation_id = conversation['id']  # Use correct field name
        self.assertIsNotNone(conversation_id)


if __name__ == '__main__':
    unittest.main()
