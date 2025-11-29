import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import os

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # We'll log JSON directly
)
logger = logging.getLogger(__name__)

def log_event(message: str, **data):
    """
    Structured logging helper that outputs JSON-formatted logs.
    Reference: https://www.dash0.com/blog/structured-logging-best-practices
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        **data
    }
    logger.info(json.dumps(log_entry))