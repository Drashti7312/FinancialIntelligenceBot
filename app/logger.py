import os
import logging
from datetime import datetime
import traceback
import inspect

def log_class() -> logging.Logger:
    logger = logging.getLogger(f"chatbot_{datetime.now().strftime('%Y-%m-%d')}.log")
    
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt='%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s - %(lineno)d'
        )

        os.makedirs("logs", exist_ok=True)

        file_handler = logging.FileHandler(
            os.path.join("logs", f"chatbot_{datetime.now().strftime('%Y-%m-%d')}.log")
        )
        file_handler.setFormatter(formatter)

        # Stream handler for printing logs to console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Add both handlers
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

def log_exception(e: Exception, logger: logging.Logger) -> dict:
    """
    Helper method to consistently log exceptions and return error response
    """
    current_function = inspect.currentframe().f_back.f_code.co_name
    tb = traceback.format_exc()
    logger.error(f"Exception occurred in {current_function}: {str(e)}\n{tb}")
    raise e

logger = log_class()
