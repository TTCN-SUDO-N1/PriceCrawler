import mysql.connector
from flask import jsonify  # Changed: Only import jsonify
import time
import functools  # Added: Import functools

# A decorator to handle database reconnection for API routes
def with_db_reconnect(max_retries=3):
    def decorator(func):
        @functools.wraps(func)  # Added: functools.wraps decorator
        def wrapper(*args, **kwargs):
            from SaveToMSQL import reconnect_if_needed
            
            for attempt in range(max_retries):
                try:
                    # Try to reconnect if needed
                    if not reconnect_if_needed():
                        if attempt < max_retries - 1:
                            print(f"Failed to reconnect to database, retrying ({attempt+1}/{max_retries})...")
                            time.sleep(1 * (attempt + 1))  # Linear backoff (comment from original)
                            continue
                        else:
                            return jsonify({"error": "Database connection failed after multiple attempts"}), 500
                    
                    # Call the original function
                    return func(*args, **kwargs)
                    
                except mysql.connector.errors.OperationalError as e:
                    print(f"Database operation error in attempt {attempt+1} for '{func.__name__}': {str(e)}")
                    if "2013" in str(e) or "2006" in str(e):  # Lost connection or server gone
                        if attempt < max_retries - 1:
                            print(f"Connection lost, retrying ({attempt+1}/{max_retries})...")
                            time.sleep(1 * (attempt + 1))
                            continue
                    
                    # If we've exhausted retries for 2013/2006 or it's a different OperationalError, return error response
                    import traceback
                    print(f"Traceback for OperationalError in '{func.__name__}':")
                    print(traceback.format_exc())
                    return jsonify({"error": f"Database error: {str(e)}"}), 500
                    
                except Exception as e:
                    import traceback
                    print(f"Unexpected error in API route '{func.__name__}': {str(e)}")
                    print(traceback.format_exc())
                    return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
            
            # Removed unreachable return statement that was here.
            # All paths should return from within the loop or its exception handlers.
            # If execution somehow reaches here, it's an unexpected state,
            # but the logic above should prevent it. For safety, one might add:
            # print(f"Error: Reached end of wrapper for '{func.__name__}' unexpectedly after {max_retries} attempts.")
            # return jsonify({"error": "Database operation failed due to an unexpected control flow"}), 500
            # However, per analysis, this should not be hit.
            
        return wrapper
    return decorator
