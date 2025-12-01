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
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_event(message: str, **data):
    """
    Structured logging helper that outputs JSON-formatted logs with color for readability.
    """
    timestamp = datetime.utcnow().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "message": message,
        **data
    }
    
    # Determine color based on message content or type
    color = Colors.BLUE
    if "ERROR" in message or "FAIL" in message:
        color = Colors.FAIL
    elif "SUCCESS" in message or "PASSED" in message:
        color = Colors.GREEN
    elif "WARNING" in message:
        color = Colors.WARNING
    elif "START" in message:
        color = Colors.CYAN
        
    # Create a readable string for console output
    readable_str = f"{Colors.BOLD}{color}[{timestamp}] {message}{Colors.ENDC}"
    
    if data:
        readable_str += f"\n{color}" + json.dumps(data, indent=2) + f"{Colors.ENDC}\n"
        readable_str += "-" * 50
        
    # Log the JSON for machine parsing (if needed) or just the readable string
    # The user asked for easier to read logs, so we'll log the readable string
    # If strict JSON logging is required for a system, we might want to separate console vs file logging
    # For this request, we prioritize readability.
    logger.info(readable_str)