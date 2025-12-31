import logging
import os
import sys


def setup_logging(name="KindleToJex", log_file="logs/app.log", level=logging.INFO):
    """
    Sets up the logging configuration.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Formatters
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # File Handler
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
