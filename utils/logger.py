"""
NEXHOST CLOUD - Logging Configuration
Author: @Harsh_54x
"""

import logging
import sys
from pathlib import Path
from config import LOGS_BASE_DIR

# Ensure log directory exists
LOGS_BASE_DIR.mkdir(parents=True, exist_ok=True)
PLATFORM_LOG_FILE = LOGS_BASE_DIR / "nexhost_platform.log"

def get_logger(name: str = "NEXHOST") -> logging.Logger:
    """Configure and return standardized logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console Handler
        c_handler = logging.StreamHandler(sys.stdout)
        c_handler.setFormatter(formatter)
        logger.addHandler(c_handler)
        
        # File Handler
        try:
            f_handler = logging.FileHandler(PLATFORM_LOG_FILE, encoding="utf-8")
            f_handler.setFormatter(formatter)
            logger.addHandler(f_handler)
        except Exception:
            pass

    return logger

logger = get_logger("NEXHOST-CORE")
