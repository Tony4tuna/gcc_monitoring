# core/logger.py
"""
Centralized logging and error handling system
"""
import logging
import traceback
from datetime import datetime
from pathlib import Path
from functools import wraps
from typing import Callable, Any
from nicegui import ui


# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Create logger
logger = logging.getLogger("gcc_monitoring")
logger.setLevel(logging.DEBUG)

# File handler - daily rotation
log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_info(message: str, module: str = "app"):
    """Log info message"""
    logger.info(f"[{module}] {message}")


def log_warning(message: str, module: str = "app"):
    """Log warning message"""
    logger.warning(f"[{module}] {message}")


def log_error(message: str, module: str = "app", exc_info: Exception = None):
    """Log error message with optional exception"""
    if exc_info:
        logger.error(f"[{module}] {message}", exc_info=exc_info)
    else:
        logger.error(f"[{module}] {message}")


def log_critical(message: str, module: str = "app", exc_info: Exception = None):
    """Log critical error"""
    if exc_info:
        logger.critical(f"[{module}] {message}", exc_info=exc_info)
    else:
        logger.critical(f"[{module}] {message}")


def handle_error(error: Exception, context: str = "operation", notify_user: bool = True) -> None:
    """
    Centralized error handler
    - Logs error with stack trace
    - Optionally notifies user with friendly message
    """
    error_msg = f"Error in {context}: {str(error)}"
    log_error(error_msg, "error_handler", exc_info=error)
    
    if notify_user:
        ui.notify(
            f"An error occurred during {context}. Please try again or contact support.",
            type="negative",
            timeout=5000
        )


def safe_execute(func: Callable, context: str = "operation", *args, **kwargs) -> Any:
    """
    Safely execute a function with error handling
    Returns None if error occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_error(e, context, notify_user=True)
        return None


def with_error_handling(context: str = "operation"):
    """
    Decorator for automatic error handling
    Usage: @with_error_handling("user creation")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context or func.__name__, notify_user=True)
                return None
        return wrapper
    return decorator


def log_user_action(action: str, details: str = "", user_id: int = None):
    """Log user actions for audit trail"""
    from core.auth import current_user
    user = current_user()
    user_email = user.get("email", "unknown") if user else "system"
    
    log_info(
        f"USER_ACTION: {action} | User: {user_email} | Details: {details}",
        module="audit"
    )


# Log startup
log_info("Logging system initialized", "logger")
