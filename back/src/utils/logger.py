import logging
import functools
import time
from pathlib import Path
from datetime import datetime
import os
import json


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "function_name": record.funcName,
            "message": record.getMessage(),
        }
        
        # Add additional fields if present
        if hasattr(record, "execution_time"):
            log_data["execution_time_seconds"] = record.execution_time
        if hasattr(record, "object_name"):
            log_data["object_name"] = record.object_name
        if hasattr(record, "arguments"):
            log_data["arguments"] = record.arguments
        if hasattr(record, "return_value"):
            log_data["return_value"] = record.return_value
        if hasattr(record, "exception"):
            log_data["exception"] = record.exception
        
        return json.dumps(log_data)


# Setup logger at module level
def _setup_logger(log_folder="logs"):
    """Setup the logger with file and console handlers."""
    # Make path absolute relative to the src directory
    if not os.path.isabs(log_folder):
        log_folder = os.path.join(os.path.dirname(__file__), "..", log_folder)
    
    log_folder = Path(log_folder)
    log_folder.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("ExecutionLogger")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # JSON formatter
    json_formatter = JSONFormatter()
    
    # File handler - logs go to a file with today's date
    log_file = log_folder / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    return logger


# Initialize the logger
_logger = _setup_logger()


def log_execution(func=None, *, message=None, object_name=None):
    """
    Decorator to wrap a function with logging and timing.
    
    Args:
        func: The function to decorate (when used without parentheses)
        message: Optional custom message to log
        object_name: Optional name of the object/class that this function belongs to
    
    Usage:
        @log_execution
        def my_function(): pass
        
        @log_execution(message="Processing data", object_name="DataManager")
        def my_function(): pass
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Prepare log information
            func_name = f.__name__
            msg = message if message else f"Function '{func_name}' executed"
            
            # Execute function and measure time
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Create a log record with execution details
                record = logging.LogRecord(
                    name="ExecutionLogger",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=msg,
                    args=(),
                    exc_info=None,
                    func=func_name,
                )
                
                # Add custom attributes to the log record
                record.execution_time = round(execution_time, 4)
                record.funcName = func_name
                if object_name:
                    record.object_name = object_name
                
                # Log successful execution
                _logger.handle(record)
                return result
            
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Create error log record
                error_record = logging.LogRecord(
                    name="ExecutionLogger",
                    level=logging.ERROR,
                    pathname="",
                    lineno=0,
                    msg=msg,
                    args=(),
                    exc_info=None,
                    func=func_name,
                )
                error_record.execution_time = round(execution_time, 4)
                error_record.funcName = func_name
                if object_name:
                    error_record.object_name = object_name
                error_record.exception = f"{type(e).__name__}: {str(e)}"
                
                # Log error
                _logger.handle(error_record)
                raise
        
        return wrapper
    
    # Support both @log_execution and @log_execution(...) syntax
    if func is not None:
        # Called as @log_execution without parentheses
        return decorator(func)
    else:
        # Called as @log_execution(...) with parentheses
        return decorator


def log_function_execution(function_name, execution_time, status="success", message=None):
    """
    Manually log a function execution with the provided execution time.
    
    Args:
        function_name (str): Name of the function
        execution_time (float): Execution time in seconds
        status (str): Status of execution ('success' or 'error')
        message (str): Custom message for the log
    """
    level = logging.ERROR if status == "error" else logging.INFO
    msg = message or f"Function '{function_name}' execution logged"
    
    record = logging.LogRecord(
        name="ExecutionLogger",
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
        func=function_name,
    )
    
    record.execution_time = round(execution_time, 4)
    record.funcName = function_name
    
    # Log it
    _logger.handle(record)
