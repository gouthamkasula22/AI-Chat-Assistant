# Testing Procedures - AI Chat Assistant

This document provides comprehensive testing procedures for the AI Chat Assistant application.

## 🧪 Testing Overview

### Testing Strategy
- **Unit Tests**: Individual component functionality
- **Integration Tests**: API endpoint testing  
- **Manual Tests**: User experience validation
- **Performance Tests**: Response time and load testing
- **Security Tests**: Input validation and error handling

## 📋 Pre-Test Setup

### Environment Preparation
```bash
# Activate virtual environment
venv\Scripts\activate

# Install test dependencies
pip install pytest pytest-mock requests-mock

# Set test environment variables
set GEMINI_API_KEY=test_key_here
```

### Test Data Preparation
```python
# Sample test conversation history
TEST_HISTORY = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you?"}
]
```

## 🔧 Unit Testing

### Running Unit Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_llm_proxy.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### LLM Proxy Tests
```python
# File: tests/test_llm_proxy.py
import pytest
from unittest.mock import patch, Mock
from services.llm_proxy import LLMProxy

class TestLLMProxy:
    def setup_method(self):
        self.proxy = LLMProxy("test_api_key")
    
    def test_send_message_success(self):
        # Test successful API response
        pass
    
    def test_send_message_timeout(self):
        # Test timeout handling
        pass
    
    def test_send_message_http_error(self):
        # Test HTTP error handling
        pass
```

### Test Coverage Goals
- **Overall Coverage**: > 80%
- **Critical Paths**: 100% (LLM communication, error handling)
- **UI Components**: > 70%

## 🌐 API Testing

### Backend API Tests

#### Health Check Test
```bash
curl -X GET http://localhost:8000/docs
# Expected: 200 OK with API documentation
```

#### Chat Endpoint Tests
```bash
# Valid request test
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"history":[{"role":"user","content":"Hello"}]}'

# Expected Response:
# {"reply": "AI response text here"}
```

#### Error Handling Tests
```bash
# Invalid JSON test
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "json"}'

# Expected: 422 Validation Error
```

#### Performance Tests
```bash
# Response time test
time curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"history":[{"role":"user","content":"Quick test"}]}'

# Target: < 5 seconds response time
```

### Load Testing
```python
# File: tests/load_test.py
import requests
import time
import concurrent.futures

def test_concurrent_requests():
    """Test multiple concurrent chat requests"""
    url = "http://localhost:8000/chat"
    payload = {"history": [{"role": "user", "content": "Load test"}]}
    
    def make_request():
        return requests.post(url, json=payload)
    
    # Test 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [future.result() for future in futures]
    
    # Verify all requests succeeded
    assert all(r.status_code == 200 for r in results)
```

## 🖥 Frontend Testing

### Manual UI Tests

#### Session Persistence Test
1. Start the application: `streamlit run main.py`
2. Send a message to the AI
3. Refresh the browser page
4. **Verify**: Previous conversation is still visible

#### Clear Chat Functionality Test
1. Have an active conversation with multiple messages
2. Click the "Clear Chat" button
3. **Verify**: All messages are cleared
4. **Verify**: New conversation can be started

#### Response Time Display Test
1. Send multiple messages to the AI
2. **Verify**: Each AI response shows response time
3. **Verify**: Response times are reasonable (< 10 seconds)

#### Error Handling Test
1. Stop the backend server (`Ctrl+C`)
2. Try to send a message from the frontend
3. **Verify**: User-friendly error message appears
4. **Verify**: Application doesn't crash

### Automated UI Tests (Optional)
```python
# File: tests/test_ui.py
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class TestStreamlitUI:
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://localhost:8501")
    
    def test_send_message(self):
        # Find input field and send message
        input_field = self.driver.find_element(By.TAG_NAME, "input")
        input_field.send_keys("Test message")
        
        # Submit message
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
        submit_button.click()
        
        # Wait for response
        time.sleep(5)
        
        # Verify response appears
        messages = self.driver.find_elements(By.CLASS_NAME, "message")
        assert len(messages) >= 2  # User message + AI response
```

## 🔒 Security Testing

### Input Validation Tests
```python
def test_malicious_input():
    """Test handling of potentially malicious input"""
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../../etc/passwd",
        "A" * 10000,  # Very long input
        "",  # Empty input
        None,  # Null input
    ]
    
    for malicious_input in malicious_inputs:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"history": [{"role": "user", "content": malicious_input}]}
        )
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 422]
```

### API Key Security Test
```bash
# Test without API key
unset GEMINI_API_KEY
python app.py

# Expected: Graceful error message, not crash
```

## 📊 Performance Testing

### Response Time Benchmarks
```python
# File: tests/performance_test.py
import time
import statistics
import requests

def test_response_times():
    """Measure and validate response times"""
    url = "http://localhost:8000/chat"
    payload = {"history": [{"role": "user", "content": "Performance test"}]}
    
    response_times = []
    
    for _ in range(10):
        start_time = time.time()
        response = requests.post(url, json=payload)
        end_time = time.time()
        
        response_times.append(end_time - start_time)
        assert response.status_code == 200
    
    # Performance assertions
    avg_time = statistics.mean(response_times)
    max_time = max(response_times)
    
    print(f"Average response time: {avg_time:.2f}s")
    print(f"Maximum response time: {max_time:.2f}s")
    
    # Performance targets
    assert avg_time < 5.0, f"Average response time too high: {avg_time}s"
    assert max_time < 10.0, f"Maximum response time too high: {max_time}s"
```

### Memory Usage Test
```python
import psutil
import os

def test_memory_usage():
    """Monitor memory usage during operation"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform multiple operations
    for i in range(100):
        # Simulate chat operations
        pass
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    print(f"Memory increase: {memory_increase:.2f} MB")
    assert memory_increase < 100, "Memory usage increase too high"
```

## 📝 Test Reports

### Test Execution Report Template
```
# Test Execution Report - AI Chat Assistant
Date: [DATE]
Tester: [NAME]
Version: [VERSION]

## Test Summary
- Total Tests: [COUNT]
- Passed: [COUNT]
- Failed: [COUNT]  
- Skipped: [COUNT]
- Coverage: [PERCENTAGE]%

## Detailed Results

### Unit Tests
- LLM Proxy: ✅ PASS
- Error Handler: ✅ PASS
- Chat Models: ✅ PASS

### API Tests  
- Chat Endpoint: ✅ PASS
- Error Handling: ✅ PASS
- Performance: ✅ PASS

### UI Tests
- Session Persistence: ✅ PASS
- Clear Chat: ✅ PASS
- Response Times: ✅ PASS

### Security Tests
- Input Validation: ✅ PASS
- API Key Protection: ✅ PASS

## Issues Found
[List any issues discovered during testing]

## Recommendations
[Any recommendations for improvements]
```

## 🚀 Continuous Integration

### GitHub Actions Workflow (Optional)
```yaml
# File: .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest tests/ --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### Local Test Script
```bash
#!/bin/bash
# File: run_tests.sh

echo "Starting comprehensive test suite..."

echo "1. Running unit tests..."
python -m pytest tests/ -v --cov=. --cov-report=html

echo "2. Running code quality checks..."
pylint . --rcfile=.pylintrc

echo "3. Running security scan..."
bandit -r . -ll

echo "4. Running dependency check..."
pip-audit

echo "5. Starting servers for integration tests..."
uvicorn app:app --port 8000 &
BACKEND_PID=$!

sleep 5

echo "6. Running API tests..."
python tests/api_tests.py

echo "7. Cleaning up..."
kill $BACKEND_PID

echo "Test suite completed!"
```

## 📈 Test Metrics & KPIs

### Success Criteria
- **Unit Test Coverage**: > 80%
- **API Response Time**: < 5 seconds average
- **UI Load Time**: < 3 seconds
- **Error Rate**: < 1% in normal operation
- **Memory Usage**: < 500MB during operation

### Performance Benchmarks
- **Concurrent Users**: Support 10 simultaneous users
- **Message Throughput**: 100 messages per minute
- **Session Persistence**: 24 hours minimum
- **Uptime Target**: 99.5% availability

---

This comprehensive testing procedure ensures the AI Chat Assistant meets all quality and performance standards before deployment.
