"""
Feedback Manager for AI Chat Assistant

This module manages user feedback collection, storage, and analysis for
continuous improvement of the AI chatbot system.
"""

import sqlite3
import json
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from utils.logger import get_logger, log_performance, log_user_interaction

logger = get_logger('feedback_manager')

class FeedbackManager:
    """Manages user feedback and learning data for the AI chatbot."""

    def __init__(self, db_path: str = "chat_history.db"):
        """Initialize feedback manager with database connection."""
        self.db_path = db_path
        self.init_feedback_tables()
        logger.info("FeedbackManager initialized", extra={
            'database_path': db_path,
            'component': 'feedback_manager'
        })

    def init_feedback_tables(self) -> None:
        """Initialize feedback-related database tables."""
        start_time = time.time()

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create message_feedback table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS message_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id INTEGER NOT NULL,
                        conversation_id INTEGER NOT NULL,
                        feedback_type TEXT NOT NULL CHECK (feedback_type IN ('thumbs_up', 'thumbs_down', 'rating', 'detailed')),
                        rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                        feedback_text TEXT,
                        ai_model_used TEXT NOT NULL,
                        conversation_style TEXT,
                        response_time REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT,
                        user_context TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                    )
                ''')

                # Create model_performance table for learning analytics
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS model_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ai_model TEXT NOT NULL,
                        conversation_style TEXT NOT NULL,
                        avg_rating REAL DEFAULT 0.0,
                        total_feedback_count INTEGER DEFAULT 0,
                        positive_feedback_count INTEGER DEFAULT 0,
                        negative_feedback_count INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0.0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        performance_score REAL DEFAULT 0.0,
                        UNIQUE(ai_model, conversation_style)
                    )
                ''')

                # Create learning_insights table for storing learning patterns
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS learning_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insight_type TEXT NOT NULL,
                        insight_data TEXT NOT NULL,
                        confidence_score REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_validated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        validation_count INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')

                # Create indexes for better performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_message_feedback_model ON message_feedback(ai_model_used)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_message_feedback_style ON message_feedback(conversation_style)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_message_feedback_timestamp ON message_feedback(timestamp)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_model_performance_score ON model_performance(performance_score DESC)')

                conn.commit()

            duration = time.time() - start_time
            log_performance("feedback_tables_initialization", duration,
                          database_path=self.db_path)
            logger.info("Feedback database tables initialized successfully")

        except sqlite3.Error as error:
            logger.error(f"Failed to initialize feedback tables: {e}", extra={
                'error_type': 'database_error',
                'operation': 'init_feedback_tables'
            })
            raise

    def add_message_feedback(self, message_id: int, conversation_id: int,
                           feedback_type: str, ai_model_used: str,
                           rating: Optional[int] = None,
                           feedback_text: Optional[str] = None,
                           conversation_style: Optional[str] = None,
                           response_time: Optional[float] = None,
                           session_id: Optional[str] = None,
                           user_context: Optional[Dict[str, Any]] = None) -> bool:
        """Add user feedback for a specific message."""
        start_time = time.time()

        try:
            with sqlite3.connect(self.db_path) as conn:
                context_json = json.dumps(user_context) if user_context else None

                conn.execute('''
                    INSERT INTO message_feedback
                    (message_id, conversation_id, feedback_type, rating, feedback_text,
                     ai_model_used, conversation_style, response_time, session_id, user_context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (message_id, conversation_id, feedback_type, rating, feedback_text,
                      ai_model_used, conversation_style, response_time, session_id, context_json))

                conn.commit()

                # Update model performance metrics
                self._update_model_performance(ai_model_used, conversation_style or 'default',
                                             feedback_type, rating)

                duration = time.time() - start_time
                log_performance("add_message_feedback", duration,
                              feedback_type=feedback_type, ai_model=ai_model_used)

                log_user_interaction(session_id or 'unknown', 'feedback_submitted',
                                   feedback_type=feedback_type, rating=rating,
                                   ai_model=ai_model_used)

                logger.info("Message feedback added successfully", extra={
                    'message_id': message_id,
                    'feedback_type': feedback_type,
                    'ai_model': ai_model_used,
                    'rating': rating
                })

                return True

        except sqlite3.Error as error:
            logger.error(f"Failed to add message feedback: {e}", extra={
                'message_id': message_id,
                'feedback_type': feedback_type,
                'error_type': 'database_error'
            })
            return False

    def _update_model_performance(self, ai_model: str, conversation_style: str,
                                feedback_type: str, rating: Optional[int]) -> None:
        """Update model performance metrics based on feedback."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current performance data
                current = conn.execute('''
                    SELECT avg_rating, total_feedback_count, positive_feedback_count,
                           negative_feedback_count, avg_response_time
                    FROM model_performance
                    WHERE ai_model = ? AND conversation_style = ?
                ''', (ai_model, conversation_style)).fetchone()

                if current:
                    # Update existing record
                    avg_rating, total_count, positive_count, negative_count, avg_response_time = current

                    new_total = total_count + 1

                    # Update rating average
                    if rating and feedback_type == 'rating':
                        new_avg_rating = ((avg_rating * total_count) + rating) / new_total
                    else:
                        new_avg_rating = avg_rating

                    # Update feedback counters
                    new_positive = positive_count + (1 if feedback_type == 'thumbs_up' else 0)
                    new_negative = negative_count + (1 if feedback_type == 'thumbs_down' else 0)

                    # Calculate performance score
                    performance_score = self._calculate_performance_score(
                        new_avg_rating, new_positive, new_negative, new_total
                    )

                    conn.execute('''
                        UPDATE model_performance
                        SET avg_rating = ?, total_feedback_count = ?,
                            positive_feedback_count = ?, negative_feedback_count = ?,
                            performance_score = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE ai_model = ? AND conversation_style = ?
                    ''', (new_avg_rating, new_total, new_positive, new_negative,
                          performance_score, ai_model, conversation_style))

                else:
                    # Create new record
                    initial_rating = rating if rating and feedback_type == 'rating' else 3.0
                    positive_count = 1 if feedback_type == 'thumbs_up' else 0
                    negative_count = 1 if feedback_type == 'thumbs_down' else 0

                    performance_score = self._calculate_performance_score(
                        initial_rating, positive_count, negative_count, 1
                    )

                    conn.execute('''
                        INSERT INTO model_performance
                        (ai_model, conversation_style, avg_rating, total_feedback_count,
                         positive_feedback_count, negative_feedback_count, performance_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (ai_model, conversation_style, initial_rating, 1,
                          positive_count, negative_count, performance_score))

                conn.commit()

        except sqlite3.Error as error:
            logger.error(f"Failed to update model performance: {e}", extra={
                'ai_model': ai_model,
                'conversation_style': conversation_style
            })

    def _calculate_performance_score(self, avg_rating: float, positive_count: int,
                                   negative_count: int, total_count: int) -> float:
        """Calculate composite performance score for model ranking."""
        if total_count == 0:
            return 0.0

        # Weighted score: 60% rating, 30% positive ratio, 10% engagement
        rating_score = (avg_rating / 5.0) * 0.6

        positive_ratio = positive_count / total_count if total_count > 0 else 0
        positive_score = positive_ratio * 0.3

        # Engagement score (more feedback = better engagement, capped at 100 feedback items)
        engagement_score = min(total_count / 100.0, 1.0) * 0.1

        return rating_score + positive_score + engagement_score

    def get_best_model_for_style(self, conversation_style: str = 'default') -> Optional[str]:
        """Get the best performing AI model for a given conversation style."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute('''
                    SELECT ai_model, performance_score, total_feedback_count
                    FROM model_performance
                    WHERE conversation_style = ? AND total_feedback_count >= 3
                    ORDER BY performance_score DESC, total_feedback_count DESC
                    LIMIT 1
                ''', (conversation_style,)).fetchone()

                if result:
                    ai_model, score, count = result
                    logger.info("Best model for style '{conversation_style}': {ai_model} (score: {score:.3f}, feedback: {count})")
                    return ai_model
                else:
                    logger.info("No sufficient feedback data for style '{conversation_style}', using default model")
                    return None

        except sqlite3.Error as error:
            logger.error("Failed to get best model for style: {error}")
            return None

    def get_feedback_analytics(self) -> Dict[str, Any]:
        """Get comprehensive feedback analytics for the dashboard."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Overall feedback statistics
                overall_stats = conn.execute('''
                    SELECT
                        COUNT(*) as total_feedback,
                        AVG(CASE WHEN rating IS NOT NULL THEN rating END) as avg_rating,
                        SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as thumbs_up,
                        SUM(CASE WHEN feedback_type = 'thumbs_down' THEN 1 ELSE 0 END) as thumbs_down
                    FROM message_feedback
                ''').fetchone()

                # Model performance comparison
                model_stats = conn.execute('''
                    SELECT ai_model, conversation_style, performance_score,
                           total_feedback_count, avg_rating
                    FROM model_performance
                    ORDER BY performance_score DESC
                ''').fetchall()

                # Recent feedback trends (last 7 days)
                recent_feedback = conn.execute('''
                    SELECT DATE(timestamp) as feedback_date, COUNT(*) as daily_count
                    FROM message_feedback
                    WHERE timestamp >= date('now', '-7 days')
                    GROUP BY DATE(timestamp)
                    ORDER BY feedback_date
                ''').fetchall()

                return {
                    'overall': {
                        'total_feedback': overall_stats[0],
                        'average_rating': round(overall_stats[1] or 0, 2),
                        'thumbs_up': overall_stats[2],
                        'thumbs_down': overall_stats[3],
                        'satisfaction_rate': round((overall_stats[2] / max(overall_stats[0], 1)) * 100, 1)
                    },
                    'model_performance': [
                        {
                            'model': row[0],
                            'style': row[1],
                            'score': round(row[2], 3),
                            'feedback_count': row[3],
                            'avg_rating': round(row[4], 2)
                        } for row in model_stats
                    ],
                    'recent_trends': [
                        {'date': row[0], 'feedback_count': row[1]}
                        for row in recent_feedback
                    ]
                }

        except sqlite3.Error as error:
            logger.error("Failed to get feedback analytics: {e}")
            return {}

    def generate_learning_insights(self) -> List[Dict[str, Any]]:
        """Generate actionable learning insights from feedback data."""
        insights = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insight 1: Underperforming models
                underperforming = conn.execute('''
                    SELECT ai_model, conversation_style, performance_score, avg_rating
                    FROM model_performance
                    WHERE performance_score < 0.5 AND total_feedback_count >= 5
                    ORDER BY performance_score ASC
                ''').fetchall()

                for model, style, score, rating in underperforming:
                    insights.append({
                        'type': 'underperforming_model',
                        'severity': 'high',
                        'message': f"Model '{model}' with style '{style}' has low performance (score: {score:.3f})",
                        'recommendation': f"Consider improving prompts or replacing model for {style} conversations",
                        'data': {'model': model, 'style': style, 'score': score, 'rating': rating}
                    })

                # Insight 2: High performing combinations
                top_performers = conn.execute('''
                    SELECT ai_model, conversation_style, performance_score
                    FROM model_performance
                    WHERE performance_score > 0.8 AND total_feedback_count >= 10
                    ORDER BY performance_score DESC
                ''').fetchall()

                for model, style, score in top_performers:
                    insights.append({
                        'type': 'high_performer',
                        'severity': 'info',
                        'message': f"Model '{model}' with style '{style}' is performing excellently (score: {score:.3f})",
                        'recommendation': f"Consider using {model} as default for {style} conversations",
                        'data': {'model': model, 'style': style, 'score': score}
                    })

                # Insight 3: Feedback volume analysis
                low_feedback_models = conn.execute('''
                    SELECT ai_model, conversation_style, total_feedback_count
                    FROM model_performance
                    WHERE total_feedback_count < 3
                ''').fetchall()

                for model, style, count in low_feedback_models:
                    insights.append({
                        'type': 'insufficient_data',
                        'severity': 'medium',
                        'message': f"Model '{model}' with style '{style}' has insufficient feedback data ({count} responses)",
                        'recommendation': "Encourage more user feedback to improve learning accuracy",
                        'data': {'model': model, 'style': style, 'feedback_count': count}
                    })

            return insights

        except sqlite3.Error as error:
            logger.error("Failed to generate learning insights: {e}")
            return []
