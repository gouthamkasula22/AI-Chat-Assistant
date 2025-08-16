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
        
        # 1. Start new conversation
        conversation_id = self.chat_service.start_new_conversation("Integration Test Chat")
        self.assertIsNotNone(conversation_id)
        
        # 2. Add user message
        user_msg_id = self.chat_service.add_user_message(
            conversation_id, "Hello AI!", "TestModel"
        )
        self.assertIsNotNone(user_msg_id)
        
        # 3. Add AI response (simulating what would happen)
        ai_response = "Hello! How can I help you today?"
        ai_msg_id = self.chat_service.add_ai_response(
            conversation_id, ai_response, "TestModel", 0.5
        )
        self.assertIsNotNone(ai_msg_id)
        
        # 4. Retrieve conversation history
        history = self.chat_service.get_conversation_history(conversation_id)
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
        
        conversation_id = self.chat_service.start_new_conversation("Multi-turn Test")
        
        # Turn 1
        self.chat_service.add_user_message(conversation_id, "What's 2+2?", "TestModel")
        self.chat_service.add_ai_response(conversation_id, "2+2 equals 4", "TestModel", 0.3)
        
        # Turn 2
        self.chat_service.add_user_message(conversation_id, "What about 3+3?", "TestModel")
        self.chat_service.add_ai_response(conversation_id, "3+3 equals 6", "TestModel", 0.4)
        
        # Verify conversation has 4 messages (2 user, 2 assistant)
        final_history = self.chat_service.get_conversation_history(conversation_id)
        self.assertEqual(len(final_history), 4)
        
        # Check message order
        self.assertEqual(final_history[0]['role'], 'user')
        self.assertEqual(final_history[1]['role'], 'assistant')
        self.assertEqual(final_history[2]['role'], 'user')
        self.assertEqual(final_history[3]['role'], 'assistant')

    def test_multiple_conversations(self):
        """Test managing multiple conversations"""
        
        # Create multiple conversations
        conv1 = self.chat_service.start_new_conversation("Math Questions")
        conv2 = self.chat_service.start_new_conversation("Programming Help")
        conv3 = self.chat_service.start_new_conversation("General Chat")
        
        # Add messages to each
        self.chat_service.add_user_message(conv1, "What's calculus?", "TestModel")
        self.chat_service.add_user_message(conv2, "How do I code in Python?", "TestModel")
        self.chat_service.add_user_message(conv3, "Hello there!", "TestModel")
        
        # Check that all conversations exist
        recent = self.chat_service.get_recent_conversations(10)
        self.assertEqual(len(recent), 3)
        
        # Check that each conversation has the right content
        conv1_history = self.chat_service.get_conversation_history(conv1)
        conv2_history = self.chat_service.get_conversation_history(conv2)
        conv3_history = self.chat_service.get_conversation_history(conv3)
        
        self.assertIn("calculus", conv1_history[0]['content'])
        self.assertIn("Python", conv2_history[0]['content'])
        self.assertIn("Hello", conv3_history[0]['content'])

    def test_conversation_persistence(self):
        """Test that conversations persist across service restarts"""
        
        # Create conversation and add messages
        conversation_id = self.chat_service.start_new_conversation("Persistence Test")
        self.chat_service.add_user_message(conversation_id, "Test message", "TestModel")
        self.chat_service.add_ai_response(conversation_id, "Test response", "TestModel", 0.2)
        
        # Create new chat service instance (simulating restart)
        new_chat_service = ChatHistoryService(self.db_manager)
        
        # Check that conversation still exists
        history = new_chat_service.get_conversation_history(conversation_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['content'], "Test message")
        self.assertEqual(history[1]['content'], "Test response")

    def test_error_handling(self):
        """Test basic error handling"""
        
        # Test getting messages from non-existent conversation
        non_existent_history = self.chat_service.get_conversation_history(99999)
        self.assertEqual(len(non_existent_history), 0)
        
        # Test that we can still create new conversations after errors
        conversation_id = self.chat_service.start_new_conversation("After Error Test")
        self.assertIsNotNone(conversation_id)


if __name__ == '__main__':
    unittest.main()
