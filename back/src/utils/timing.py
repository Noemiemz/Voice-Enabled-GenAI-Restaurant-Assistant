"""
Timing utilities for monitoring LLM performance
"""
import time
from functools import wraps
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional


def time_operation(operation_name: Optional[str] = None):
    """Decorator to measure and log function execution time.
    
    Args:
        operation_name: Custom name for the operation. If None, uses function name.
        
    Returns:
        Decorator function that wraps the original function with timing logic.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Log the timing
                log_timing(operation_name or func.__name__, execution_time)
            
            return result
        return wrapper
    return decorator


def log_timing(operation: str, duration: float, context: Optional[Dict[str, Any]] = None):
    """Log timing information to a performance log file.
    
    Args:
        operation: Name of the operation being timed
        duration: Duration in seconds
        context: Additional context data to include in the log
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "duration_seconds": round(duration, 6),
        "context": context or {}
    }

    try:
        # Get the directory where this file is located
        current_dir = Path(__file__).parent.parent
        log_dir = current_dir / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"performance_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
    except Exception as e:
        print(f"[TIMING] Error logging timing: {e}")


def start_timing(operation: str):
    """Start timing an operation manually.
    
    Returns:
        A tuple of (operation_name, start_time) that can be passed to end_timing()
    """
    return (operation, time.time())


def end_timing(start_info: tuple, context: Optional[Dict[str, Any]] = None):
    """End timing an operation manually.
    
    Args:
        start_info: Tuple returned by start_timing()
        context: Additional context data
    """
    operation, start_time = start_info
    duration = time.time() - start_time
    log_timing(operation, duration, context)