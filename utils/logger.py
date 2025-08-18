#!/usr/bin/env python3
"""
Comprehensive Logging System for AI Chat Assistant
Provides structured logging with multiple handlers and formatters.
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

import traceback

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "process_id": record.process
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Format the message
        formatted = f"{color}[{timestamp}] {record.levelname:8} {reset}"
        formatted += f"{color}[{record.name}]{reset} "
        formatted += f"{record.getMessage()}"

        # Add location info for DEBUG level
        if record.levelno == logging.DEBUG:
            formatted += f" {color}({record.module}:{record.funcName}:{record.lineno}){reset}"

        return formatted


class ChatLogger:
    """Main logging manager for the AI Chat Assistant."""

    def __init__(self, name: str = "ai_chat_assistant"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Setup all logging handlers."""

        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        # 1. Console Handler (with colors)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)

        # 2. General Application Log (rotating file)
        app_handler = logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, "app.log"),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
        ))
        self.logger.addHandler(app_handler)

        # 3. Error Log (for errors and above)
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, "errors.log"),
            maxBytes=5*1024*1024,   # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(error_handler)

        # 4. Performance Log (for timing and metrics)
        perf_handler = logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, "performance.log"),
            maxBytes=5*1024*1024,   # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(JSONFormatter())
        self.performance_logger = logging.getLogger(f"{self.name}.performance")
        self.performance_logger.addHandler(perf_handler)
        self.performance_logger.setLevel(logging.INFO)

        # 5. Security Log (for security events)
        security_handler = logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, "security.log"),
            maxBytes=5*1024*1024,   # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(JSONFormatter())
        self.security_logger = logging.getLogger(f"{self.name}.security")
        self.security_logger.addHandler(security_handler)
        self.security_logger.setLevel(logging.WARNING)

    def get_logger(self, module_name: str = None) -> logging.Logger:
        """Get a logger for a specific module."""
        if module_name:
            return logging.getLogger(f"{self.name}.{module_name}")
        return self.logger

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        extra_data = {
            "operation": operation,
            "duration_seconds": duration,
            "performance_metric": True,
            **kwargs
        }

        # Create a log record with extra data
        record = logging.LogRecord(
            name=self.performance_logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Performance: {operation} completed in {duration:.3f}s",
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data
        self.performance_logger.handle(record)

    def log_security_event(self, event_type: str, details: Dict[str, Any], level: int = logging.WARNING):
        """Log security-related events."""
        extra_data = {
            "security_event": True,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }

        record = logging.LogRecord(
            name=self.security_logger.name,
            level=level,
            pathname="",
            lineno=0,
            msg=f"Security Event: {event_type}",
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data
        self.security_logger.handle(record)

    def log_user_interaction(self, session_id: str, action: str, **kwargs):
        """Log user interactions."""
        extra_data = {
            "user_interaction": True,
            "session_id": session_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"User Interaction: {action}",
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data
        self.logger.handle(record)

    def log_ai_response(self, model: str, input_length: int, output_length: int,
                       response_time: float, session_id: str, **kwargs):
        """Log AI model responses."""
        extra_data = {
            "ai_response": True,
            "model": model,
            "input_length": input_length,
            "output_length": output_length,
            "response_time": response_time,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"AI Response: {model} processed {input_length} chars -> {output_length} chars in {response_time:.3f}s",
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data
        self.logger.handle(record)

    def log_database_operation(self, operation: str, table: str, duration: float, **kwargs):
        """Log database operations."""
        extra_data = {
            "database_operation": True,
            "operation": operation,
            "table": table,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg=f"Database: {operation} on {table} completed in {duration:.3f}s",
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data
        self.logger.handle(record)


# Global logger instance
_global_logger = None

def get_logger(module_name: str = None) -> logging.Logger:
    """Get the global logger instance."""
    global _global_logger

    if _global_logger is None:
        _global_logger = ChatLogger()

    return _global_logger.get_logger(module_name)

def get_chat_logger() -> ChatLogger:
    """Get the ChatLogger instance."""
    global _global_logger

    if _global_logger is None:
        _global_logger = ChatLogger()

    return _global_logger

def log_performance(operation: str, duration: float, **kwargs):
    """Convenience function for performance logging."""
    chat_logger = get_chat_logger()
    chat_logger.log_performance(operation, duration, **kwargs)

def log_security_event(event_type: str, details: Dict[str, Any], level: int = logging.WARNING):
    """Convenience function for security logging."""
    chat_logger = get_chat_logger()
    chat_logger.log_security_event(event_type, details, level)

def log_user_interaction(session_id: str, action: str, **kwargs):
    """Convenience function for user interaction logging."""
    chat_logger = get_chat_logger()
    chat_logger.log_user_interaction(session_id, action, **kwargs)

def log_ai_response(model: str, input_length: int, output_length: int,
                   response_time: float, session_id: str, **kwargs):
    """Convenience function for AI response logging."""
    chat_logger = get_chat_logger()
    chat_logger.log_ai_response(model, input_length, output_length, response_time, session_id, **kwargs)

def log_database_operation(operation: str, table: str, duration: float, **kwargs):
    """Convenience function for database operation logging."""
    chat_logger = get_chat_logger()
    chat_logger.log_database_operation(operation, table, duration, **kwargs)
