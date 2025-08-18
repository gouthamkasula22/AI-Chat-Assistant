"""
Feedback UI Components for AI Chat Assistant

Professional UI components for collecting user feedback without animations.
"""

from typing import Optional, Dict, Any

import streamlit as st

from database.feedback_manager import FeedbackManager
from utils.logger import get_logger, log_user_interaction

logger = get_logger('feedback_ui')

class FeedbackUI:
    """Professional UI components for collecting user feedback."""

    def __init__(self, feedback_manager: FeedbackManager):
        self.feedback_manager = feedback_manager

    def render_message_feedback(self, message_id: int, conversation_id: int,
                              ai_model_used: str, conversation_style: str,
                              response_time: float, session_id: str) -> None:
        """Render feedback UI for a specific message."""
        feedback_key = f"feedback_{message_id}"

        # Create columns for feedback buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        with col1:
            if st.button("👍", key=f"thumbs_up_{message_id}", help="Good response"):
                self._submit_feedback(
                    message_id, conversation_id, "thumbs_up", ai_model_used,
                    conversation_style, response_time, session_id
                )
                st.success("Feedback received")
                st.rerun()

        with col2:
            if st.button("👎", key=f"thumbs_down_{message_id}", help="Poor response"):
                self._submit_feedback(
                    message_id, conversation_id, "thumbs_down", ai_model_used,
                    conversation_style, response_time, session_id
                )
                st.info("Feedback received")
                st.rerun()

        with col3:
            if st.button("⭐", key=f"detailed_{message_id}", help="Detailed feedback"):
                st.session_state[f"show_detailed_{message_id}"] = True
                st.rerun()

        # Detailed feedback form
        if st.session_state.get(f"show_detailed_{message_id}", False):
            self._render_detailed_feedback_form(
                message_id, conversation_id, ai_model_used,
                conversation_style, response_time, session_id
            )

    def _render_detailed_feedback_form(self, message_id: int, conversation_id: int,
                                     ai_model_used: str, conversation_style: str,
                                     response_time: float, session_id: str) -> None:
        """Render detailed feedback form."""
        with st.expander("Detailed Feedback", expanded=True):
            rating = st.select_slider(
                "Rate this response:",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: "⭐" * x,
                key=f"rating_{message_id}"
            )

            feedback_text = st.text_area(
                "Additional comments (optional):",
                placeholder="What did you like or dislike about this response?",
                key=f"feedback_text_{message_id}",
                max_chars=500
            )

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("Submit Feedback", key=f"submit_detailed_{message_id}"):
                    success = self._submit_feedback(
                        message_id, conversation_id, "rating", ai_model_used,
                        conversation_style, response_time, session_id,
                        rating=rating, feedback_text=feedback_text
                    )

                    if success:
                        st.success("Feedback submitted successfully")
                        st.session_state[f"show_detailed_{message_id}"] = False
                        st.rerun()
                    else:
                        st.error("Failed to submit feedback. Please try again.")

            with col2:
                if st.button("Cancel", key=f"cancel_detailed_{message_id}"):
                    st.session_state[f"show_detailed_{message_id}"] = False
                    st.rerun()

    def _submit_feedback(self, message_id: int, conversation_id: int,
                        feedback_type: str, ai_model_used: str,
                        conversation_style: str, response_time: float,
                        session_id: str, rating: Optional[int] = None,
                        feedback_text: Optional[str] = None) -> bool:
        """Submit feedback to the database."""

        user_context = {
            'message_count': len(st.session_state.get('messages', [])),
            'response_time': response_time,
            'timestamp': str(st.session_state.get('conversation_started', 'unknown'))
        }

        success = self.feedback_manager.add_message_feedback(
            message_id=message_id,
            conversation_id=conversation_id,
            feedback_type=feedback_type,
            ai_model_used=ai_model_used,
            rating=rating,
            feedback_text=feedback_text,
            conversation_style=conversation_style,
            response_time=response_time,
            session_id=session_id,
            user_context=user_context
        )

        if success:
            log_user_interaction(session_id, f"feedback_{feedback_type}",
                               message_id=message_id, rating=rating,
                               ai_model=ai_model_used)
            logger.info("User feedback submitted successfully", extra={
                'feedback_type': feedback_type,
                'ai_model': ai_model_used,
                'rating': rating
            })

        return success

    def render_feedback_analytics_sidebar(self) -> None:
        """Render feedback analytics in the sidebar."""
        with st.sidebar.expander("Feedback Analytics", expanded=False):
            analytics = self.feedback_manager.get_feedback_analytics()

            if analytics.get('overall'):
                overall = analytics['overall']

                st.metric("Total Feedback", overall['total_feedback'])
                st.metric("Average Rating", f"{overall['average_rating']}/5.0")
                st.metric("Satisfaction Rate", f"{overall['satisfaction_rate']}%")

                # Feedback distribution
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Positive", overall['thumbs_up'])
                with col2:
                    st.metric("Negative", overall['thumbs_down'])

                # Top performing models
                if analytics.get('model_performance'):
                    st.subheader("Top Models")
                    for model_data in analytics['model_performance'][:3]:
                        st.write(f"**{model_data['model']}** ({model_data['style']})")
                        st.write(f"Score: {model_data['score']:.3f} | Count: {model_data['feedback_count']}")
            else:
                st.info("No feedback data available yet")

    def render_learning_insights(self) -> None:
        """Render learning insights dashboard."""
        st.subheader("Learning Insights")

        insights = self.feedback_manager.generate_learning_insights()

        if not insights:
            st.info("No insights available yet. More feedback data needed for analysis.")
            return

        # Group insights by severity
        high_severity = [i for i in insights if i['severity'] == 'high']
        medium_severity = [i for i in insights if i['severity'] == 'medium']
        info_severity = [i for i in insights if i['severity'] == 'info']

        # High severity insights (problems to fix)
        if high_severity:
            st.error("Issues Requiring Attention:")
            for insight in high_severity:
                with st.container():
                    st.write(f"**{insight['message']}**")
                    st.write(f"Recommendation: {insight['recommendation']}")
                    st.divider()

        # Medium severity insights (improvements)
        if medium_severity:
            st.warning("Areas for Improvement:")
            for insight in medium_severity:
                with st.container():
                    st.write(f"**{insight['message']}**")
                    st.write(f"Recommendation: {insight['recommendation']}")
                    st.divider()

        # Positive insights (what's working well)
        if info_severity:
            st.success("What's Working Well:")
            for insight in info_severity:
                with st.container():
                    st.write(f"**{insight['message']}**")
                    st.write(f"Recommendation: {insight['recommendation']}")
                    st.divider()
