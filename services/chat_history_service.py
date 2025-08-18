"""
Chat History Service

This service layer provides high-level operations for managing chat history.
It acts as an interface between the UI layer and the database layer,
implementing business logic for chat operations.

Key Features:
- Session-based conversation management
- Automatic conversation creation
- Message persistence with timing
- History retrieval and management
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from database.db_manager import DatabaseManager

# Configure logging
logger = logging.getLogger(__name__)


class ChatHistoryService:
    """
    Service class for managing chat history operations.

    This class provides business logic for:
    - Managing conversations and sessions
    - Storing and retrieving messages
    - Generating conversation titles
    - Handling data migration from JSON files
    """

    def __init__(self, db_path: str = "chat_history.db"):
        """
        Initialize the chat history service.

        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_manager = DatabaseManager(db_path)
        logger.info("Chat history service initialized")

    def start_or_resume_conversation(self, session_id: str,
                                   ai_model: str = "gemini-pro") -> Dict[str, Any]:
        """
        Start a new conversation or resume an existing one for a session.

        This method implements the core business logic:
        1. Check if a conversation exists for the session
        2. If not, create a new one
        3. Return conversation details

        Args:
            session_id (str): Unique session identifier
            ai_model (str): AI model to use for the conversation

        Returns:
            Dict[str, Any]: Conversation details including ID and metadata
        """
        try:
            # Try to get existing conversation
            conversation = self.db_manager.get_conversation_by_session(session_id)

            if conversation:
                logger.info("Resuming conversation {conversation['id']} for session {session_id}")
                return conversation

            # Create new conversation
            conversation_id = self.db_manager.create_conversation(
                session_id=session_id,
                title="New Chat",  # Will be updated with first user message
                ai_model=ai_model
            )

            # Get the created conversation
            conversation = self.db_manager.get_conversation_by_session(session_id)
            logger.info("Started new conversation {conversation_id} for session {session_id}")

            return conversation

        except Exception as error:
            logger.error("Failed to start/resume conversation: {e}")
            raise

    def add_user_message(self, session_id: str, content: str) -> Dict[str, Any]:
        """
        Add a user message to the conversation.

        Args:
            session_id (str): Session identifier
            content (str): Message content

        Returns:
            Dict[str, Any]: Message details including ID and timestamp
        """
        try:
            conversation = self.start_or_resume_conversation(session_id)
            conversation_id = conversation['id']

            # Add the message
            message_id = self.db_manager.add_message(
                conversation_id=conversation_id,
                role="user",
                content=content
            )

            # Update conversation title if this is the first user message
            if conversation['total_messages'] == 0:
                title = self._generate_conversation_title(content)
                self._update_conversation_title(conversation_id, title)

            logger.info("Added user message to conversation {conversation_id}")

            return {
                'id': message_id,
                'conversation_id': conversation_id,
                'role': 'user',
                'content': content,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as error:
            logger.error("Failed to add user message: {e}")
            raise

    def add_assistant_message(self, session_id: str, content: str,
                            response_time: float = 0.0) -> Dict[str, Any]:
        """
        Add an assistant message to the conversation.

        Args:
            session_id (str): Session identifier
            content (str): Message content
            response_time (float): Time taken to generate the response

        Returns:
            Dict[str, Any]: Message details including ID and timing
        """
        try:
            conversation = self.start_or_resume_conversation(session_id)
            conversation_id = conversation['id']

            message_id = self.db_manager.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=content,
                response_time=response_time
            )

            logger.info("Added assistant message to conversation {conversation_id}")

            return {
                'id': message_id,
                'conversation_id': conversation_id,
                'role': 'assistant',
                'content': content,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as error:
            logger.error("Failed to add assistant message: {e}")
            raise

    def get_conversation_history(self, session_id: str,
                               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the complete conversation history for a session.

        Args:
            session_id (str): Session identifier
            limit (Optional[int]): Maximum number of messages to return

        Returns:
            List[Dict[str, Any]]: List of messages in chronological order
        """
        try:
            conversation = self.db_manager.get_conversation_by_session(session_id)
            if not conversation:
                return []

            messages = self.db_manager.get_conversation_messages(
                conversation_id=conversation['id'],
                limit=limit
            )

            logger.info("Retrieved {len(messages)} messages for session {session_id}")
            return messages

        except Exception as error:
            logger.error("Failed to get conversation history: {e}")
            return []

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversations for the sidebar/history view.

        Args:
            limit (int): Maximum number of conversations to return

        Returns:
            List[Dict[str, Any]]: List of recent conversations
        """
        try:
            conversations = self.db_manager.get_recent_conversations(limit)
            logger.info("Retrieved {len(conversations)} recent conversations")
            return conversations

        except Exception as error:
            logger.error("Failed to get recent conversations: {e}")
            return []

    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id (int): ID of conversation to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            success = self.db_manager.delete_conversation(conversation_id)
            if success:
                logger.info("Deleted conversation {conversation_id}")
            return success

        except Exception as error:
            logger.error("Failed to delete conversation: {e}")
            return False

    def _generate_conversation_title(self, first_message: str, max_length: int = 50) -> str:
        """
        Generate a meaningful title from the first user message.

        This is a simple implementation that:
        1. Takes the first sentence or phrase
        2. Truncates to a reasonable length
        3. Adds ellipsis if truncated

        Args:
            first_message (str): The first user message
            max_length (int): Maximum title length

        Returns:
            str: Generated conversation title
        """
        # Remove extra whitespace
        title = first_message.strip()

        # Take first sentence if available
        if '.' in title:
            title = title.split('.')[0]
        elif '?' in title:
            title = title.split('?')[0] + '?'
        elif '!' in title:
            title = title.split('!')[0] + '!'

        # Truncate if too long
        if len(title) > max_length:
            title = title[:max_length-3] + "..."

        return title if title else "New Chat"

    def _update_conversation_title(self, conversation_id: int, title: str) -> bool:
        """
        Update the title of a conversation.

        Args:
            conversation_id (int): ID of the conversation
            title (str): New title

        Returns:
            bool: True if updated successfully
        """
        try:
            with self.db_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE conversations
                    SET title = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (title, conversation_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as error:
            logger.error("Failed to update conversation title: {e}")
            return False

    def migrate_from_session_files(self, session_files_pattern: str = "temp_session_*.json") -> int:
        """
        Migrate existing JSON session files to the database.

        This method helps users transition from file-based storage to database storage
        by importing their existing conversation history.

        Args:
            session_files_pattern (str): Glob pattern for session files

        Returns:
            int: Number of conversations migrated
        """
        import json
        import glob

        migrated_count = 0

        try:
            for file_path in glob.glob(session_files_pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)

                    session_id = session_data.get('session_id')
                    messages = session_data.get('messages', [])

                    if not session_id or not messages:
                        continue

                    # Create conversation
                    conversation = self.start_or_resume_conversation(session_id)
                    conversation_id = conversation['id']

                    # Add messages
                    for message in messages:
                        self.db_manager.add_message(
                            conversation_id=conversation_id,
                            role=message.get('role', 'user'),
                            content=message.get('content', ''),
                            response_time=0.0
                        )

                    # Update title if we have messages
                    if messages and messages[0].get('role') == 'user':
                        title = self._generate_conversation_title(messages[0]['content'])
                        self._update_conversation_title(conversation_id, title)

                    migrated_count += 1
                    logger.info("Migrated session file: {file_path}")

                except (json.JSONDecodeError, KeyError) as error:
                    logger.warning("Failed to migrate {file_path}: {e}")
                    continue

            logger.info("Migration completed: {migrated_count} conversations migrated")
            return migrated_count

        except Exception as error:
            logger.error("Migration failed: {e}")
            return migrated_count

    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the chat history service.

        Returns:
            Dict[str, Any]: Service statistics and health information
        """
        try:
            db_stats = self.db_manager.get_database_stats()

            return {
                'database_stats': db_stats,
                'service_status': 'healthy',
                'features': [
                    'session_persistence',
                    'conversation_management',
                    'message_storage',
                    'history_retrieval'
                ]
            }

        except Exception as error:
            logger.error("Failed to get service stats: {e}")
            return {
                'database_stats': {'conversations': 0, 'messages': 0, 'db_size_bytes': 0},
                'service_status': 'error',
                'error': str(e)
            }
