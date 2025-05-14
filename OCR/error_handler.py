"""
Error handler utility for the Flask application
"""
import logging
import traceback
import mysql.connector
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app_errors.log'
)

logger = logging.getLogger('price_tracker')

# Error types for categorization
class ErrorTypes:
    DATABASE = "database_error"
    NETWORK = "network_error"
    CRAWL = "crawl_error"
    VALIDATION = "validation_error"
    AUTH = "auth_error"
    PERMISSION = "permission_error"
    UNKNOWN = "unknown_error"

def log_error(error, error_type=ErrorTypes.UNKNOWN, user_id=None, additional_info=None):
    """
    Log an error with contextual information
    
    Args:
        error: The exception or error object
        error_type: Type of error for categorization
        user_id: Optional user ID for tracking who encountered the error
        additional_info: Any additional context about the error
    """
    error_details = {
        'timestamp': datetime.now().isoformat(),
        'error_type': error_type,
        'error_message': str(error),
        'user_id': user_id,
        'additional_info': additional_info,
        'traceback': traceback.format_exc()
    }
    
    # Log to file
    logger.error(f"Error: {error_type} - {str(error)}")
    if additional_info:
        logger.error(f"Context: {additional_info}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return error_details

def handle_database_error(error, operation=None):
    """
    Handle MySQL database errors
    
    Args:
        error: The database exception
        operation: Description of the database operation that failed
    """
    if isinstance(error, mysql.connector.Error):
        # Handle specific MySQL error codes
        if error.errno == 1045:  # Access denied
            message = "Database access denied. Please check credentials."
        elif error.errno == 1049:  # Unknown database
            message = "Database does not exist."
        elif error.errno == 1062:  # Duplicate entry
            message = "Duplicate entry. This record already exists."
        elif error.errno == 1064:  # SQL syntax error
            message = "Invalid SQL query."
        elif error.errno == 2003:  # Connection refused
            message = "Cannot connect to database server."
        else:
            message = f"Database error: {str(error)}"
    else:
        message = f"Database operation failed: {str(error)}"
    
    log_error(
        error, 
        error_type=ErrorTypes.DATABASE,
        additional_info=operation
    )
    
    return message

def handle_crawl_error(error, url=None):
    """
    Handle errors that occur during web crawling
    
    Args:
        error: The exception
        url: URL that was being crawled
    """
    if "timeout" in str(error).lower():
        message = "Connection timed out. The website might be slow or unresponsive."
    elif "connection" in str(error).lower():
        message = "Failed to connect to the website. Please check the URL or try again later."
    elif "blocked" in str(error).lower() or "captcha" in str(error).lower():
        message = "Website access blocked. The website might have detected automated access."
    else:
        message = f"Error crawling website: {str(error)}"
    
    log_error(
        error, 
        error_type=ErrorTypes.CRAWL,
        additional_info=f"Failed to crawl URL: {url}"
    )
    
    return message

def format_user_friendly_error(error, error_type=ErrorTypes.UNKNOWN):
    """
    Format an error message to be user-friendly
    
    Args:
        error: The exception or error message
        error_type: Type of error for appropriate message formatting
    """
    if error_type == ErrorTypes.DATABASE:
        return handle_database_error(error)
    elif error_type == ErrorTypes.CRAWL:
        return handle_crawl_error(error)
    elif error_type == ErrorTypes.VALIDATION:
        return f"Validation error: {str(error)}"
    elif error_type == ErrorTypes.NETWORK:
        return "Network error. Please check your connection and try again."
    elif error_type == ErrorTypes.AUTH:
        return "Authentication failed. Please log in again."
    elif error_type == ErrorTypes.PERMISSION:
        return "You don't have permission to perform this action."
    else:
        # For unknown errors, provide a generic message
        return "An unexpected error occurred. Please try again later."
