import mysql.connector
import json as js
import db_config as dbconf
import time
from mysql.connector import pooling

# Create a connection pool with 5 connections
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        pool_reset_session=True,
        host=dbconf.DB_CONFIG['host'],
        user=dbconf.DB_CONFIG['user'],
        password=dbconf.DB_CONFIG['password'],
        database=dbconf.DB_CONFIG['database'],
        connect_timeout=30,
        connection_timeout=300  # Increase timeout to handle longer queries
    )
    print("Connection pool created successfully")
except mysql.connector.Error as err:
    print(f"Failed to create connection pool: {err}")
    connection_pool = None

def get_connection_from_pool():
    """Get a connection from the connection pool"""
    if connection_pool:
        try:
            return connection_pool.get_connection()
        except mysql.connector.Error as err:
            print(f"Error getting connection from pool: {err}")
    return None

def connect_to_database():
    """Connect to the MySQL database with retry mechanism"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # First try to get a connection from the pool
            if connection_pool:
                conn = get_connection_from_pool()
                if conn and conn.is_connected():
                    print("Successfully got connection from pool")
                    return conn
            
            # If pool doesn't exist or fails, create a new connection
            connection = mysql.connector.connect(
                host=dbconf.DB_CONFIG['host'],
                user=dbconf.DB_CONFIG['user'],
                password=dbconf.DB_CONFIG['password'],
                database=dbconf.DB_CONFIG['database'],
                connect_timeout=30,
                connection_timeout=300  # Increase timeout to handle longer queries
            )
            
            if connection.is_connected():
                print("Successfully connected to the database")
                return connection
            elif dbconf.CREATE_IF_NOT_EXISTS:
                print("Database not found, creating a new one...")
                connection = mysql.connector.connect(
                    host=dbconf.DB_CONFIG['host'],
                    user=dbconf.DB_CONFIG['user'],
                    password=dbconf.DB_CONFIG['password']
                )
                cursor = connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {dbconf.DB_CONFIG['database']}")
                connection.database = dbconf.DB_CONFIG['database']
                with open(dbconf.SQL_SCHEMA_PATH, 'r') as sql_file:
                    sql_script = sql_file.read()
                for statement in sql_script.split(';'):
                    if statement.strip():
                        cursor.execute(statement)
                connection.commit()
                cursor.close()
                print(f"Database '{dbconf.DB_CONFIG['database']}' created successfully")
                return connection
            else:
                print("Failed to connect to the database")
                return None
        
        except mysql.connector.Error as err:
            print(f"Connection attempt {attempt+1} failed: {err}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("All connection attempts failed")
                return None
    
    return None

# Initial connection
connection = connect_to_database()

def reconnect_if_needed():
    """Check if connection is alive, and reconnect if necessary"""
    global connection
    try:
        if connection is None or not connection.is_connected():
            print("Database connection lost. Reconnecting...")
            connection = connect_to_database()
            return connection is not None
        return True
    except mysql.connector.Error:
        print("Error checking connection. Attempting to reconnect...")
        connection = connect_to_database()
        return connection is not None

def clean_price(price):
    """Convert price string (e.g., '16.490.000 VNĐ') to decimal value"""
    if price is None or price == '':
        return None
        
    # Handle non-string inputs
    if not isinstance(price, str):
        try:
            # If it's already a number, return it directly
            return float(price)
        except (ValueError, TypeError):
            return None
            
    try:
        # First, try to standardize the format
        # Remove currency symbols and non-numeric characters except for decimal separators
        cleaned_price = price.replace('$', '').replace('€', '').replace('VND', '').replace('₫', '').replace('VNĐ', '').strip()
        
        # Remove any remaining letters or special characters (except . and ,)
        import re
        cleaned_price = re.sub(r'[^0-9.,]', '', cleaned_price)
        
        # Handle empty string after cleaning
        if not cleaned_price:
            return None
        
        # Handle Vietnamese number format with periods as thousand separators and commas as decimal separators
        # Example: "16.490.000" -> "16490000"
        if '.' in cleaned_price and ',' not in cleaned_price:
            cleaned_price = cleaned_price.replace('.', '')
        # Example: "7,790,000" -> "7790000"
        elif ',' in cleaned_price and '.' not in cleaned_price:
            cleaned_price = cleaned_price.replace(',', '')
        # Example: "1.234,56" -> "1234.56" (European format)
        elif ',' in cleaned_price and '.' in cleaned_price:
            # If both are present, assume European format (. for thousands, , for decimal)
            cleaned_price = cleaned_price.replace('.', '').replace(',', '.')
            
        # Convert to float - if empty string at this point, return None
        if cleaned_price.strip() == '':
            return None
            
        return float(cleaned_price)
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Error converting price '{price}' to float: {e}")
        return None


def save_originals(data):
    global connection
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Handle different input types
            if isinstance(data, str):
                # Assume it's a file path
                with open(data, 'r', encoding='utf-8') as f:
                    json_data = js.load(f)
            elif hasattr(data, 'read'):
                # File-like object
                json_data = js.load(data)
            else:
                # Assume it's already loaded data
                json_data = data
                
            if not json_data:
                print("No data to save")
                return
            
            # Check and reconnect if needed
            if not reconnect_if_needed():
                print("Failed to reconnect to database")
                time.sleep(1)  # Wait before retry
                retry_count += 1
                continue
                
            cursor = connection.cursor()
            
            # Process the JSON data
            if isinstance(json_data, list):
                items_to_process = json_data
            elif isinstance(json_data, dict) and 'products' in json_data:
                items_to_process = json_data['products']
            elif isinstance(json_data, dict):
                # Single product as a dictionary
                items_to_process = [json_data]
            else:
                print(f"Unexpected JSON structure: {type(json_data)}")
                print(f"Data preview: {str(json_data)[:200]}")
                return
                
            for item in items_to_process:
                # Extract product details
                name = item.get('product_name', '')
                sku = item.get('sku', '')
                link = item.get('link', '')
                
                # Process prices
                current_price_str = item.get('current_price', '')
                promo_price_str = item.get('promotional_price', '')
                
                print(f"Processing product: {name}")
                print(f"SKU: {sku}")
                print(f"Raw current price: {current_price_str}")
                print(f"Raw promotional price: {promo_price_str}")
                
                current_price = clean_price(current_price_str)
                promo_price = clean_price(promo_price_str)
                
                print(f"Cleaned current price: {current_price}")
                print(f"Cleaned promotional price: {promo_price}")
                
                # Use promo_price as current_price if available, otherwise use current_price for both
                org_price = current_price
                cur_price = promo_price if promo_price else current_price
                
                # Skip products without a name
                if not name:
                    print("Skipping item without a name")
                    print(f"Item data: {item}")
                    continue
                    
                # Generate a unique SKU if empty
                if not sku:
                    # Create a SKU based on the product name (first letters of each word + timestamp)
                    import re
                    import time
                    words = re.findall(r'\b\w+\b', name)
                    prefix = ''.join(word[0].upper() for word in words if word)
                    timestamp = int(time.time())
                    sku = f"{prefix}{timestamp}"
                    print(f"Generated unique SKU: {sku} for product: {name}")
                
                    
                # Instead of checking if product already exists, always create a new product
                # Generate a unique SKU for every product
                import time
                import re
                words = re.findall(r'\b\w+\b', name)
                prefix = ''.join(word[0].upper() for word in words if word)
                timestamp = int(time.time())
                sku = f"{prefix}{timestamp}"
                print(f"Generated unique SKU: {sku} for product: {name}")
                
                try:
                    # Insert the new product - always create a new one
                    cursor.execute(
                        "INSERT INTO products (name, sku, link, org_price, cur_price) VALUES (%s, %s, %s, %s, %s)",
                        (name, sku, link, org_price, cur_price)
                    )
                    print(f"Inserted new product: {name} with SKU: {sku}")
                except mysql.connector.IntegrityError as err:
                    print(f"Integrity error when saving product: {err}")
             
            connection.commit()
            print("Data saved successfully")
            return True
            
        except mysql.connector.errors.OperationalError as err:
            # Handle connection errors specifically
            print(f"Database connection error when saving originals (attempt {retry_count+1}): {err}")
            connection = connect_to_database()  # Try to reconnect
            retry_count += 1
            if retry_count < max_retries:
                print(f"Retrying... ({retry_count}/{max_retries})")
                time.sleep(1 * retry_count)  # Exponential backoff
            else:
                print("Max retries reached. Giving up.")
                return False
     
        except mysql.connector.Error as err:
            if isinstance(err, mysql.connector.IntegrityError):
                print(f"Integrity error: {err}")
                if connection and connection.is_connected():
                    connection.rollback()
            else:
                print(f"Database error: {err}")
                if connection and connection.is_connected():
                    connection.rollback()
            return False
            
        except Exception as e:
            print(f"General error: {e}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
            
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
    
    return False

def save_enemy(name, domain):
    """
    Save or update enemy information in the database
    
    Args:
        data: Dictionary containing enemy information with at least 'name' and 'domain'
    """
    global connection
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check and reconnect if needed
            if not reconnect_if_needed():
                print("Failed to reconnect to database")
                time.sleep(1)  # Wait before retry
                retry_count += 1
                continue
                
            cursor = connection.cursor()
          
            if not name or not domain:
                print("Enemy data must include both name and domain")
                return False
                
            # Check if enemy already exists
            cursor.execute("SELECT id FROM enemies WHERE domain = %s", (domain,))
            existing_enemy = cursor.fetchone()
            
            if existing_enemy:
                # Update existing enemy
                cursor.execute(
                    "UPDATE enemies SET name = %s WHERE domain = %s",
                    (name, domain)
                )
                enemy_id = existing_enemy[0]
                print(f"Updated enemy: {name} ({domain})")
            else:
                # Insert new enemy
                cursor.execute(
                    "INSERT INTO enemies (name, domain) VALUES (%s, %s)",
                    (name, domain)
                )
                # Get the ID of the newly inserted enemy
                enemy_id = cursor.lastrowid
                print(f"Added new enemy: {name} ({domain})")
                
            connection.commit()
            return enemy_id
            
        except mysql.connector.errors.OperationalError as err:
            # Handle connection errors specifically
            print(f"Database connection error when saving enemy (attempt {retry_count+1}): {err}")
            connection = connect_to_database()  # Try to reconnect
            retry_count += 1
            if retry_count < max_retries:
                print(f"Retrying... ({retry_count}/{max_retries})")
                time.sleep(1 * retry_count)  # Exponential backoff
            else:
                print("Max retries reached. Giving up.")
                return False
            
        except mysql.connector.Error as err:
            print(f"Database error when saving enemy: {err}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
            
        except Exception as e:
            print(f"General error when saving enemy: {e}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
            
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
    
    return False


def save_product_crawl(product_id, enemy_id, link):
    """
    Save relationship between product and enemy website (crawl source)
    
    Args:
        product_id: ID of the product in the products table
        enemy_id: ID of the enemy in the enemies table
        link: URL where the product was found
        
    Returns:
        The ID of the crawl relationship in the database
    """
    global connection
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check and reconnect if needed
            if not reconnect_if_needed():
                print("Failed to reconnect to database")
                time.sleep(1)  # Wait before retry
                retry_count += 1
                continue
                
            cursor = connection.cursor()
            
            # Create new relationship - we don't check for existing ones since
            # we want to add all products from all enemies
            cursor.execute(
                "INSERT INTO product_crawls (prod_id, enemy_id, link) VALUES (%s, %s, %s)",
                (product_id, enemy_id, link)
            )
            crawl_id = cursor.lastrowid
            print(f"Created new product crawl relationship (ID: {crawl_id})")
                
            connection.commit()
            return crawl_id
            
        except mysql.connector.errors.OperationalError as err:
            # Handle connection errors specifically
            print(f"Database connection error when saving product crawl (attempt {retry_count+1}): {err}")
            connection = connect_to_database()  # Try to reconnect
            retry_count += 1
            if retry_count < max_retries:
                print(f"Retrying... ({retry_count}/{max_retries})")
                time.sleep(1 * retry_count)  # Exponential backoff
            else:
                print("Max retries reached. Giving up.")
                return False
                
        except mysql.connector.Error as err:
            print(f"Database error when saving product crawl: {err}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
            
        except Exception as e:
            print(f"General error when saving product crawl: {e}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
            
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
    
    return False

def save_product_crawl_log(crawl_id, data):
    """
    Save a log of product information from a crawl
    
    Args:
        crawl_id: ID of the product crawl in the product_crawls table
        data: Dictionary or list of product information
        
    Returns:
        List of IDs for the created log entries
    """
    global connection
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check if crawl_id is valid
            if not crawl_id:
                print("Cannot save crawl log: Invalid crawl_id")
                return False
                
            # Handle different input types
            if isinstance(data, str):
                # Assume it's a file path
                with open(data, 'r', encoding='utf-8') as f:
                    json_data = js.load(f)
            elif hasattr(data, 'read'):
                # File-like object
                json_data = js.load(data)
            else:
                # Assume it's already loaded data
                json_data = data
                
            if not json_data:
                print("No data to save")
                return []
                
            # Check and reconnect if needed
            if not reconnect_if_needed():
                print("Failed to reconnect to database")
                time.sleep(1)  # Wait before retry
                retry_count += 1
                continue
            
            cursor = connection.cursor()
            
            # Process the JSON data
            if isinstance(json_data, list):
                items_to_process = json_data
            elif isinstance(json_data, dict) and 'products' in json_data:
                items_to_process = json_data['products']
            elif isinstance(json_data, dict):
                # Single product as dictionary
                items_to_process = [json_data]
            else:
                print(f"Unexpected JSON structure in save_product_crawl_log: {type(json_data)}")
                print(f"Data preview: {str(json_data)[:200]}")
                return []
                
            log_ids = []
            for item in items_to_process:
                # Extract product details
                name = item.get('product_name', '')
                sku = item.get('sku', '')
                link = item.get('link', '')
                
                if not name:
                    print("Skipping log entry without a product name")
                    continue
                    
                # Process prices - try multiple fields that might contain price information
                price_candidates = [
                    item.get('current_price', ''),
                    item.get('promotional_price', ''),
                    item.get('price', ''),
                    item.get('sale_price', ''),
                    item.get('giá', ''),
                    item.get('giá bán', '')
                ]
                
                # Use the first non-empty price found
                current_price_str = next((p for p in price_candidates if p), '')
                
                print(f"Processing crawl log for: {name}")
                print(f"Raw current price: {current_price_str}")
                
                current_price = clean_price(current_price_str)
                print(f"Cleaned price: {current_price}")
                
                # Store everything else as JSON in other_data, excluding common fields
                exclude_fields = ['product_name', 'current_price', 'promotional_price', 'link', 'price', 'sale_price', 'giá', 'giá bán']
                other_data = {k: v for k, v in item.items() if k not in exclude_fields}
                
                try:
                    # Insert log entry
                    cursor.execute(
                        "INSERT INTO product_crawl_logs (product_crawl_id, name, price, other_data) VALUES (%s, %s, %s, %s)",
                        (crawl_id, name, current_price, js.dumps(other_data))
                    )
                    
                    log_id = cursor.lastrowid
                    log_ids.append(log_id)
                    print(f"Added log entry for product: {name} (ID: {log_id})")
                    
                    # Update the product_crawls timestamp
                    cursor.execute("UPDATE product_crawls SET updated_at = CURRENT_TIMESTAMP WHERE id = %s", (crawl_id,))
                    
                except mysql.connector.Error as e:
                    print(f"Database error saving log for {name}: {e}")
                    # Continue with other items even if one fails
            
            connection.commit()
            return log_ids
            
        except mysql.connector.errors.OperationalError as err:
            # Handle connection errors specifically
            print(f"Database connection error when saving product crawl log (attempt {retry_count+1}): {err}")
            connection = connect_to_database()  # Try to reconnect
            retry_count += 1
            if retry_count < max_retries:
                print(f"Retrying... ({retry_count}/{max_retries})")
                time.sleep(1 * retry_count)  # Exponential backoff
            else:
                print("Max retries reached. Giving up.")
                return False
                
        except mysql.connector.Error as err:
            print(f"Database error when saving crawl log: {err}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
            
        except Exception as e:
            print(f"General error when saving crawl log: {e}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
            
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
    
    return False
