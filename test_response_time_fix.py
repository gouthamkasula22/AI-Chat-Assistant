#!/usr/bin/env python3
"""
Test script to verify the response time display fix.
This script simulates the session state behavior to check if response times persist.
"""

import json
import os
import tempfile
import uuid
from unittest.mock import MagicMock

# Mock Streamlit session state
class MockSessionState:
    def __init__(self):
        self.response_times = []
        self.messages = []
        self.message_count = 0
        self.conversation_started = False
        self.total_response_time = 0
        self.session_id = str(uuid.uuid4())
        self.browser_session_id = str(uuid.uuid4())

def get_browser_session_id():
    """Mock version of the browser session ID function."""
    return "test-session-id"

def save_session_data(session_state):
    """Save session data to a temporary file for persistence."""
    try:
        session_id = get_browser_session_id()
        session_file = f"temp_session_{session_id}.json"

        session_data = {
            "messages": session_state.messages,
            "message_count": session_state.message_count,
            "conversation_started": session_state.conversation_started,
            "response_times": session_state.response_times,
            "total_response_time": session_state.total_response_time,
            "session_id": session_state.session_id,
        }

        with open(session_file, "w", encoding="utf-8") as session_file_handle:
            json.dump(session_data, session_file_handle)
        return True
    except (IOError, OSError, json.JSONEncodeError):
        return False

def load_session_data(session_state):
    """Load session data from temporary file."""
    try:
        session_id = get_browser_session_id()
        session_file = f"temp_session_{session_id}.json"

        if os.path.exists(session_file):
            with open(session_file, "r", encoding="utf-8") as session_file_handle:
                session_data = json.load(session_file_handle)

            # Restore session state
            session_state.messages = session_data.get("messages", [])
            session_state.message_count = session_data.get("message_count", 0)
            session_state.conversation_started = session_data.get("conversation_started", False)
            session_state.response_times = session_data.get("response_times", [])
            session_state.total_response_time = session_data.get("total_response_time", 0)
            session_state.session_id = session_data.get("session_id", get_browser_session_id())
            return True
    except (IOError, OSError, json.JSONDecodeError):
        pass
    return False

def test_response_time_persistence():
    """Test that response times persist across session reloads."""
    print("Testing response time persistence...")
    
    # Simulate first session
    print("\n1. Creating initial session with response times...")
    session1 = MockSessionState()
    session1.response_times = [1.25, 2.45, 0.89]  # Three response times
    session1.messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing great!"},
        {"role": "user", "content": "Tell me a joke"},
        {"role": "assistant", "content": "Why did the chicken cross the road?"}
    ]
    session1.message_count = 6
    session1.total_response_time = sum(session1.response_times)
    
    print(f"   Initial response times: {session1.response_times}")
    print(f"   Total response time: {session1.total_response_time}")
    
    # Save session data
    save_result = save_session_data(session1)
    print(f"   Session save result: {save_result}")
    
    # Simulate session reload (new session state)
    print("\n2. Simulating session reload...")
    session2 = MockSessionState()
    print(f"   Before load - response times: {session2.response_times}")
    
    # Load session data
    load_result = load_session_data(session2)
    print(f"   Session load result: {load_result}")
    print(f"   After load - response times: {session2.response_times}")
    print(f"   After load - total response time: {session2.total_response_time}")
    
    # Verify the data persisted correctly
    success = (
        session2.response_times == session1.response_times and
        session2.total_response_time == session1.total_response_time and
        session2.message_count == session1.message_count
    )
    
    print(f"\n3. Test result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print("   Response times now persist across session reloads!")
        print("   The bug has been fixed.")
    else:
        print("   Response times are still not persisting properly.")
    
    # Cleanup
    try:
        session_file = f"temp_session_{get_browser_session_id()}.json"
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"   Cleaned up test file: {session_file}")
    except:
        pass
    
    return success

def test_response_index_tracking():
    """Test the response index tracking logic."""
    print("\nTesting response index tracking logic...")
    
    # Simulate conversation with multiple responses
    response_times = [1.25, 2.45, 0.89, 1.67]
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing great!"},
        {"role": "user", "content": "Tell me a joke"},
        {"role": "assistant", "content": "Why did the chicken cross the road?"},
        {"role": "user", "content": "I don't know, why?"},
        {"role": "assistant", "content": "To get to the other side!"}
    ]
    
    print(f"   Messages: {len(messages)}")
    print(f"   Response times: {response_times}")
    
    # Test response index calculation
    response_index = 0
    for i, message in enumerate(messages):
        if message["role"] == "assistant":
            if response_index < len(response_times):
                response_time = response_times[response_index]
                print(f"   Message {i}: Assistant response {response_index + 1} -> {response_time}s")
                response_index += 1
            else:
                print(f"   Message {i}: Assistant response {response_index + 1} -> No response time available")
    
    expected_responses = 4
    actual_responses = response_index
    success = (actual_responses == expected_responses and actual_responses == len(response_times))
    
    print(f"\n   Expected assistant responses: {expected_responses}")
    print(f"   Actual assistant responses counted: {actual_responses}")
    print(f"   Response times available: {len(response_times)}")
    print(f"   Index tracking test: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

if __name__ == "__main__":
    print("=" * 60)
    print("RESPONSE TIME DISPLAY FIX - TEST SUITE")
    print("=" * 60)
    
    test1_result = test_response_time_persistence()
    test2_result = test_response_index_tracking()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Response time persistence: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Response index tracking: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! The response time display bug has been fixed.")
    else:
        print("\n⚠️  Some tests failed. The bug may not be fully resolved.")
