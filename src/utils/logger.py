"""
Centralized logging configuration for Second Brain Agent.

This module provides consistent logging setup across the application
with support for both console and file logging.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# ANSI color codes for terminal output
class LogColors:
    """ANSI color codes for colored terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    COLORS = {
        logging.DEBUG: LogColors.CYAN,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.RED + LogColors.BOLD,
    }

    def format(self, record):
        """Format log record with colors."""
        # Get the color for this log level
        color = self.COLORS.get(record.levelno, LogColors.WHITE)

        # Format the log message
        record.levelname = f"{color}{record.levelname}{LogColors.RESET}"
        record.name = f"{LogColors.BLUE}{record.name}{LogColors.RESET}"

        return super().format(record)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
    use_colors: bool = True,
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_string: Custom format string for log messages
        use_colors: Whether to use colored output for console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # Remove any existing handlers

    # Default format string
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if use_colors and sys.stdout.isatty():
        console_formatter = ColoredFormatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    else:
        console_formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)

        # File logs don't need colors
        file_formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one with default settings."""
    return logging.getLogger(name)


# Global logger instance
_loggers = {}


def get_default_log_dir() -> Path:
    """Get the default directory for log files."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


def setup_project_logger(
    component: str = "main", level: int = logging.INFO, enable_file_logging: bool = True
) -> logging.Logger:
    """
    Set up a project-specific logger with standardized configuration.

    Args:
        component: Component name (e.g., 'architect', 'dev_team', 'curator')
        level: Logging level
        enable_file_logging: Whether to enable file logging

    Returns:
        Configured logger
    """
    logger_name = f"second_brain.{component}"

    if logger_name in _loggers:
        return _loggers[logger_name]

    log_file = None
    if enable_file_logging:
        log_dir = get_default_log_dir()
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"{component}_{timestamp}.log"

    logger = setup_logger(logger_name, level=level, log_file=log_file)
    _loggers[logger_name] = logger

    return logger
