import os
import logging
from rich.logging import RichHandler


LOG_FILE_PATH = None


def setup_logs_folder(unique_dir):
    global LOG_FILE_PATH
    # Ensure the base logs directory exists
    logs_dir = os.path.join(unique_dir, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Define the log file path within the unique UUID directory
    LOG_FILE_PATH = os.path.join(logs_dir, "readmate.log")


def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Disable propagation to higher-level (root) logger
    logger.propagate = False

    # Clear all handlers
    logger.handlers = []

    handler = RichHandler(rich_tracebacks=True)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # FileHandler for saving logs to a file

    if LOG_FILE_PATH:
        file_handler = logging.FileHandler(LOG_FILE_PATH)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.addHandler(handler)
    return logger
