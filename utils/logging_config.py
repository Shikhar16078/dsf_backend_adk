import logging
import os
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    os.makedirs("logs", exist_ok=True)

    # Get current time and format as HH:MM AM/PM
    timestamp = datetime.now().strftime("%I-%M %p")  # Use "-" instead of ":" for file compatibility
    log_filename = f"logs/{timestamp}.log"

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if already set
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.propagate = False

    return logger