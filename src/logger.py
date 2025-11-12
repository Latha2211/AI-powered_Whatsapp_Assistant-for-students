"""
Logger Setup - Centralized logging configuration
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import colorlog


def setup_logger(name: str, log_level: str = None) -> logging.Logger:
    """
    Setup logger with colored console output and file logging
    
    Args:
        name: Logger name (usually module name)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    
    # Get log level from environment or default to INFO
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory
    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Console handler with colors
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    console_format = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_format)
    
    # File handler with rotation
    log_file = os.path.join(log_dir, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def log_bot_action(bot_name: str, action: str, status: str = "info"):
    """
    Log bot actions to a separate bot activity log
    
    Args:
        bot_name: Name of the bot
        action: Action description
        status: Log level (info, success, warning, error)
    """
    
    bot_logger = logging.getLogger(f"bot.{bot_name}")
    
    status_map = {
        "info": bot_logger.info,
        "success": bot_logger.info,
        "warning": bot_logger.warning,
        "error": bot_logger.error
    }
    
    log_func = status_map.get(status, bot_logger.info)
    
    # Add emoji prefix
    emoji_map = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    prefix = emoji_map.get(status, "")
    log_func(f"{prefix} {action}")
