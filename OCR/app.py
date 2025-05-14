from flask import Flask, request, jsonify, render_template
import mysql.connector
import os
from urllib.parse import urlparse
from datetime import datetime
import SaveToMSQL as db  # Import your existing database module
import screenshot  # Import your screenshot module # Import your text extraction module
import error_handler as err  # Import the new error handler
from db_reconnect import with_db_reconnect  # Import our reconnection decorator

app = Flask(__name__)

# Ensure the templates directory exists
os.makedirs('templates', exist_ok=True)

# Move main.html to templates directory if it's not already there
if os.path.exists('main.html') and not os.path.exists('templates/main.html'):
    import shutil
    shutil.copy('main.html', 'templates/main.html')

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/products')
def products_page():
    """Show all products page"""
    return render_template('products.html')

@app.route('/api/products', methods=['GET'])
@with_db_reconnect(max_retries=3)
def get_products():
    """Get all products with pagination"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 50:  # Limit max items per page
        per_page = 10
        
    # Calculate offset
    offset = (page - 1) * per_page
    
    connection = db.connection
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get total count for pagination
        cursor.execute("SELECT COUNT(*) as total FROM products")
        total = cursor.fetchone()['total']
        
        # Get paginated products
        cursor.execute(
            "SELECT id, name, sku, link, org_price, cur_price, created_at, updated_at FROM products ORDER BY name LIMIT %s OFFSET %s", 
            (per_page, offset)
        )
        products = cursor.fetchall()
        
        # Format prices and dates for display
        for product in products:
            # Create raw copies of prices for sorting/calculations
            if product['org_price'] is not None:
                product['org_price_raw'] = product['org_price']
                try:
                    product['org_price'] = f"{product['org_price']:,.0f} VND"
                except (ValueError, TypeError):
                    product['org_price'] = "Invalid price"
            else:
                product['org_price_raw'] = 0
                product['org_price'] = "N/A"
                
            if product['cur_price'] is not None:
                product['cur_price_raw'] = product['cur_price']
                try:
                    product['cur_price'] = f"{product['cur_price']:,.0f} VND"
                except (ValueError, TypeError):
                    product['cur_price'] = "Invalid price"
            else:
                product['cur_price_raw'] = 0
                product['cur_price'] = "N/A"
                
            # Format dates safely
            if product['created_at'] is not None:
                try:
                    product['created_at'] = product['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                except:
                    product['created_at'] = str(product['created_at'])
                    
            if product['updated_at'] is not None:
                try:
                    product['updated_at'] = product['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                except:
                    product['updated_at'] = str(product['updated_at'])
        
        # Calculate pagination metadata
        total_pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1
        
        return jsonify({
            "products": products,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        })
        
    finally:
        if cursor:
            cursor.close()

@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({"error": "Product name is required"}), 400
            
        # Convert prices to float
        org_price = clean_price(data.get('org_price', ''))
        cur_price = clean_price(data.get('cur_price', ''))
        
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = connection.cursor()
        
        # Insert new product
        cursor.execute(
            "INSERT INTO products (name, sku, link, org_price, cur_price) VALUES (%s, %s, %s, %s, %s)",
            (data.get('name'), data.get('sku'), data.get('link'), org_price, cur_price)
        )
        
        product_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        
        return jsonify({
            "id": product_id, 
            "message": "Product added successfully",
            "product": {
                "id": product_id,
                "name": data.get('name'),
                "sku": data.get('sku'),
                "link": data.get('link'),
                "org_price": data.get('org_price'),
                "cur_price": data.get('cur_price')
            }
        })
        
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product"""
    try:
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Get product details
        cursor.execute("SELECT id, name, sku, link, org_price, cur_price FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
            
        # Format prices for display
        if product['org_price'] is not None:
            product['org_price'] = f"{product['org_price']:,.0f} VND"
        if product['cur_price'] is not None:
            product['cur_price'] = f"{product['cur_price']:,.0f} VND"
        
        cursor.close()
        
        return jsonify({"product": product})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    try:
        data = request.json
        
        # Convert prices to float
        org_price = clean_price(data.get('org_price', ''))
        cur_price = clean_price(data.get('cur_price', ''))
        
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = connection.cursor()
        
        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Product not found"}), 404
            
        # Update product
        cursor.execute(
            "UPDATE products SET name = %s, sku = %s, link = %s, org_price = %s, cur_price = %s WHERE id = %s",
            (data.get('name'), data.get('sku'), data.get('link'), org_price, cur_price, product_id)
        )
        
        connection.commit()
        cursor.close()
        
        return jsonify({"message": "Product updated successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = connection.cursor()
        
        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Product not found"}), 404
            
        # Delete product (related records will be deleted via cascading)
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        
        connection.commit()
        cursor.close()
        
        return jsonify({"message": "Product deleted successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<int:product_id>/enemies', methods=['GET'])
@with_db_reconnect(max_retries=3)
def get_product_enemies(product_id):
    """Get all enemy products for a specific product"""
    connection = db.connection
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Product not found"}), 404
            
        # Get enemy products
        query = """
        SELECT 
            pc.id AS crawl_id,
            e.id AS enemy_id,
            e.name AS enemy_name,
            e.domain AS enemy_domain,
            pc.link,
            pc.created_at,
            pc.updated_at,
            (SELECT COUNT(*) FROM product_crawl_logs WHERE product_crawl_id = pc.id) AS log_count,
            (SELECT price FROM product_crawl_logs 
             WHERE product_crawl_id = pc.id 
             ORDER BY timestamp DESC LIMIT 1) AS latest_price,
            (SELECT timestamp FROM product_crawl_logs 
             WHERE product_crawl_id = pc.id 
             ORDER BY timestamp DESC LIMIT 1) AS last_updated_at
        FROM 
            product_crawls pc
        JOIN 
            enemies e ON pc.enemy_id = e.id
        WHERE 
            pc.prod_id = %s
        ORDER BY 
            e.name ASC
        """
        
        cursor.execute(query, (product_id,))
        enemies = cursor.fetchall()
        
        # Format data and handle potential None values
        for enemy in enemies:
            # Set default price trend
            enemy['price_trend'] = 'unknown'
            
            # Format timestamps
            if enemy['created_at']:
                enemy['created_at'] = enemy['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if enemy['updated_at']:
                enemy['updated_at'] = enemy['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            if enemy['last_updated_at']:
                enemy['last_updated_at'] = enemy['last_updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Format price
            if enemy['latest_price'] is not None:
                enemy['price_display'] = f"{enemy['latest_price']:,.0f} VND"
            else:
                enemy['price_display'] = "N/A"
            
            # Only check price trends if we have enough logs
            if enemy['log_count'] and enemy['log_count'] >= 2:
                crawl_id = enemy['crawl_id']
                
                # Get the two most recent price logs for this crawl
                cursor.execute("""
                    SELECT price, timestamp 
                    FROM product_crawl_logs 
                    WHERE product_crawl_id = %s AND price IS NOT NULL
                    ORDER BY timestamp DESC 
                    LIMIT 2
                """, (crawl_id,))
                
                price_logs = cursor.fetchall()
                
                # Determine price trend if we have at least 2 price points with valid prices
                if len(price_logs) >= 2 and price_logs[0]['price'] is not None and price_logs[1]['price'] is not None:
                    current_price = price_logs[0]['price']
                    previous_price = price_logs[1]['price']
                    
                    if current_price > previous_price:
                        enemy['price_trend'] = 'up'
                    elif current_price < previous_price:
                        enemy['price_trend'] = 'down'
                    else:
                        enemy['price_trend'] = 'same'
        
        # Sort enemies by price (handling None values)
        enemies = sorted(enemies, key=lambda x: (x['latest_price'] is None, x['latest_price'] or 0))
        
        return jsonify({"enemies": enemies})
        
    finally:
        if cursor:
            cursor.close()

@app.route('/api/products/<int:product_id>/enemies', methods=['POST'])
def add_product_enemy(product_id):
    """Add a new enemy product for a specific product"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('link'):
            return jsonify({"error": "Link is required"}), 400
            
        link = data.get('link')
        
        # Extract domain from URL
        parsed_url = urlparse(link)
        domain = parsed_url.netloc
        
        # Extract name from domain
        enemy_name = domain.split(".")[-2] if len(domain.split(".")) > 1 else domain
        
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500
            
        # Check if product exists
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Product not found"}), 404
            
        # Save enemy information
        enemy_id = db.save_enemy(enemy_name, domain)
        
        if not enemy_id:
            return jsonify({"error": "Failed to save enemy information"}), 500
            
        # Save product-enemy relationship
        crawl_id = db.save_product_crawl(product_id, enemy_id, link)
        
        if not crawl_id:
            return jsonify({"error": "Failed to save product-enemy relationship"}), 500
            
        # Start the crawling process
        # This is typically an asynchronous operation, but for simplicity, we'll do it synchronously
        try:
            screenshot.scrape(link, is_original=False, enemy_name=enemy_name, enemy_domain=domain)
            crawl_status = "completed"
        except Exception as e:
            crawl_status = f"error: {str(e)}"
        
        return jsonify({
            "crawl_id": crawl_id,
            "enemy_id": enemy_id,
            "enemy_name": enemy_name,
            "domain": domain,
            "link": link,
            "crawl_status": crawl_status,
            "message": "Enemy link added and processed"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crawl', methods=['POST'])
def crawl_url():
    """Crawl a specific URL"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('url'):
            return jsonify({"error": "URL is required"}), 400
            
        url = data.get('url')
        crawl_id = data.get('crawl_id')
        is_original = data.get('is_original', False)
        
        # Start the crawling process
        try:
            if is_original:
                # For original products
                product_name = data.get('product_name')
                product_sku = data.get('product_sku')
                screenshot.scrape(url, is_original=True, product_name=product_name, product_sku=product_sku)
            else:
                # For enemy products
                # Extract domain from URL
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                # Extract name from domain
                enemy_name = domain.split(".")[-2] if len(domain.split(".")) > 1 else domain
                
                screenshot.scrape(url, is_original=False, enemy_name=enemy_name, enemy_domain=domain)
                
            crawl_status = "completed"
        except Exception as e:
            crawl_status = f"error: {str(e)}"
        
        return jsonify({
            "url": url,
            "crawl_id": crawl_id,
            "is_original": is_original,
            "crawl_status": crawl_status,
            "message": "URL crawled successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crawl/all/<int:product_id>', methods=['POST'])
def crawl_all_enemies(product_id):
    """Crawl all enemy products for a specific product"""
    try:
        connection = db.connection
        if not connection or not connection.is_connected():
            error_msg = err.handle_database_error(Exception("Database connection failed"), "Connect to database")
            return jsonify({"error": error_msg}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Check if product exists
        cursor.execute("SELECT id, name FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({"error": "Product not found"}), 404
            
        # Get all enemy links for this product
        cursor.execute(
            """
            SELECT pc.id AS crawl_id, pc.link, e.name AS enemy_name, e.domain AS enemy_domain
            FROM product_crawls pc
            JOIN enemies e ON pc.enemy_id = e.id
            WHERE pc.prod_id = %s
            """, 
            (product_id,)
        )
        
        crawls = cursor.fetchall()
        cursor.close()
        
        if not crawls:
            return jsonify({"message": "No competitor products found for this product"}), 404
            
        results = []
        successful_crawls = 0
        for crawl in crawls:
            # Crawl each URL with enhanced error handling
            result = {
                "crawl_id": crawl['crawl_id'],
                "link": crawl['link'],
                "enemy_name": crawl['enemy_name'],
                "status": "pending",
                "error": None
            }
            
            try:
                # Use the enhanced crawl function that returns a status dict
                crawl_result = screenshot.scrape(
                    crawl['link'], 
                    is_original=False,
                    enemy_name=crawl['enemy_name'],
                    enemy_domain=crawl['enemy_domain']
                )
                
                # Update result with crawl status
                if crawl_result.get("success"):
                    result["status"] = "completed"
                    successful_crawls += 1
                else:
                    result["status"] = "failed"
                    result["error"] = crawl_result.get("error") or "Unknown error during crawl"
                    
                    # Log the error with our error handler
                    err.log_error(
                        Exception(result["error"]), 
                        error_type=err.ErrorTypes.CRAWL,
                        additional_info=f"Failed crawling {crawl['link']} for product {product['name']}"
                    )
            except Exception as e:
                # Catch any unexpected exceptions
                error_message = err.handle_crawl_error(e, crawl['link'])
                result["status"] = "failed"
                result["error"] = error_message
            
            results.append(result)
        
        return jsonify({
            "message": f"Crawled {successful_crawls} of {len(results)} competitor products",
            "product_id": product_id,
            "product_name": product['name'],
            "success_count": successful_crawls,
            "total_count": len(results),
            "results": results
        })
        
    except mysql.connector.Error as db_err:
        error_msg = err.handle_database_error(db_err, f"Crawl all enemies for product {product_id}")
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_details = err.log_error(e, err.ErrorTypes.UNKNOWN)
        return jsonify({
            "error": f"An unexpected error occurred during crawl operation",
            "error_id": error_details.get('timestamp', '')
        }), 500

@app.route('/api/crawl/single/<int:crawl_id>', methods=['POST'])
def crawl_single_url(crawl_id):
    """Crawl a single competitor product URL"""
    try:
        connection = db.connection
        if not connection or not connection.is_connected():
            error_msg = err.handle_database_error(Exception("Database connection failed"), "Connect to database")
            return jsonify({"error": error_msg}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Get the crawl data with product and enemy info
        query = """
        SELECT 
            pc.id AS crawl_id, 
            pc.link, 
            pc.prod_id,
            p.name AS product_name,
            e.name AS enemy_name, 
            e.domain AS enemy_domain
        FROM 
            product_crawls pc
        JOIN 
            products p ON pc.prod_id = p.id
        JOIN 
            enemies e ON pc.enemy_id = e.id
        WHERE 
            pc.id = %s
        """
        
        cursor.execute(query, (crawl_id,))
        crawl_data = cursor.fetchone()
        cursor.close()
        
        if not crawl_data:
            return jsonify({"error": "Crawl record not found"}), 404
            
        # Execute the crawl with enhanced error handling
        result = {
            "crawl_id": crawl_id,
            "product_id": crawl_data['prod_id'],
            "product_name": crawl_data['product_name'],
            "link": crawl_data['link'],
            "enemy_name": crawl_data['enemy_name'],
            "status": "pending",
            "error": None,
            "timestamp": None
        }
        
        try:
            # Use the enhanced crawl function
            crawl_result = screenshot.scrape(
                crawl_data['link'], 
                is_original=False,
                enemy_name=crawl_data['enemy_name'],
                enemy_domain=crawl_data['enemy_domain']
            )
            
            # Update result with crawl status
            if crawl_result.get("success"):
                result["status"] = "completed"
                result["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                result["status"] = "failed"
                result["error"] = crawl_result.get("error") or "Unknown error during crawl"
                
                # Log the error
                err.log_error(
                    Exception(result["error"]), 
                    error_type=err.ErrorTypes.CRAWL,
                    additional_info=f"Failed crawling {crawl_data['link']} for product {crawl_data['product_name']}"
                )
        except Exception as e:
            # Catch any unexpected exceptions
            error_message = err.handle_crawl_error(e, crawl_data['link'])
            result["status"] = "failed"
            result["error"] = error_message
        
        return jsonify(result)
        
    except mysql.connector.Error as db_err:
        error_msg = err.handle_database_error(db_err, f"Crawl single URL for crawl ID {crawl_id}")
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_details = err.log_error(e, err.ErrorTypes.UNKNOWN)
        return jsonify({
            "error": f"An unexpected error occurred during crawl operation",
            "error_id": error_details.get('timestamp', '')
        }), 500

@app.route('/api/products/<int:product_id>/with-competitors', methods=['GET'])
def get_product_with_competitors(product_id):

    try:
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500  
        cursor = connection.cursor(dictionary=True)
        
        # Get the original product
        cursor.execute(
            "SELECT id, name, sku, link, org_price, cur_price, created_at, updated_at FROM products WHERE id = %s",
            (product_id,)
        )
        product = cursor.fetchone()
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
            
        # Format price for display
        if product['org_price'] is not None:
            product['org_price'] = f"{product['org_price']:,.0f} VND"
        if product['cur_price'] is not None:
            product['cur_price'] = f"{product['cur_price']:,.0f} VND"
            
        # Format dates
        product['created_at'] = product['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        product['updated_at'] = product['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Get all competitor products (with the latest price for each)
        competitor_query = """
        SELECT 
            pc.id AS crawl_id,
            e.id AS enemy_id,
            e.name AS competitor_name,
            e.domain AS competitor_domain,
            pc.link AS competitor_link,
            pcl.name AS product_name,
            pcl.price AS competitor_price,
            pcl.timestamp AS last_updated,
            (SELECT COUNT(*) FROM product_crawl_logs 
             WHERE product_crawl_id = pc.id) AS crawl_count
        FROM 
            product_crawls pc
        JOIN 
            enemies e ON pc.enemy_id = e.id
        LEFT JOIN (
            SELECT 
                product_crawl_id,
                name,
                price,
                timestamp,
                ROW_NUMBER() OVER (PARTITION BY product_crawl_id ORDER BY timestamp DESC) as rn
            FROM 
                product_crawl_logs
        ) pcl ON pc.id = pcl.product_crawl_id AND pcl.rn = 1
        WHERE 
            pc.prod_id = %s
        ORDER BY
            competitor_price ASC
        """
        
        cursor.execute(competitor_query, (product_id,))
        competitors = cursor.fetchall()
        
        # Format competitor data
        for comp in competitors:
            if comp['competitor_price'] is not None:
                comp['competitor_price'] = f"{comp['competitor_price']:,.0f} VND"
            if comp['last_updated'] is not None:
                comp['last_updated'] = comp['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                comp['last_updated'] = "Never"
        
        # Get price history (all crawl logs)
        history_query = """
        SELECT 
            e.name AS competitor_name,
            pcl.name AS product_name,
            pcl.price,
            pcl.timestamp,
            pcl.other_data
        FROM 
            product_crawl_logs pcl
        JOIN 
            product_crawls pc ON pcl.product_crawl_id = pc.id
        JOIN 
            enemies e ON pc.enemy_id = e.id
        WHERE 
            pc.prod_id = %s
        ORDER BY 
            pcl.timestamp DESC
        LIMIT 50
        """
        
        cursor.execute(history_query, (product_id,))
        price_history = cursor.fetchall()
        
        # Format price history
        for hist in price_history:
            if hist['price'] is not None:
                hist['price'] = f"{hist['price']:,.0f} VND"
            hist['timestamp'] = hist['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        
        return jsonify({
            "product": product,
            "competitors": competitors,
            "price_history": price_history,
            "total_competitors": len(competitors),
            "lowest_price": min([comp['competitor_price'] for comp in competitors], default=None) if competitors else None,
            "highest_price": max([comp['competitor_price'] for comp in competitors], default=None) if competitors else None
        })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/search', methods=['GET'])
def search_products():
    """Search for products by name"""
    try:
        query = request.args.get('q', '')
        if not query or len(query) < 2:
            return jsonify({"error": "Search query must be at least 2 characters"}), 400
            
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Search for products by name
        cursor.execute(
            """
            SELECT id, name, sku, link, org_price, cur_price 
            FROM products 
            WHERE name LIKE %s OR sku LIKE %s
            ORDER BY name
            LIMIT 20
            """, 
            (f"%{query}%", f"%{query}%")
        )
        products = cursor.fetchall()
        
        # Format prices
        for product in products:
            if product['org_price'] is not None:
                product['org_price'] = f"{product['org_price']:,.0f} VND"
            if product['cur_price'] is not None:
                product['cur_price'] = f"{product['cur_price']:,.0f} VND"
        
        # Get competitor count for each product
        for product in products:
            cursor.execute(
                "SELECT COUNT(*) as count FROM product_crawls WHERE prod_id = %s",
                (product['id'],)
            )
            product['competitor_count'] = cursor.fetchone()['count']
        
        cursor.close()
        
        return jsonify({
            "query": query,
            "products": products,
            "count": len(products)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<int:product_id>/price-history', methods=['GET'])
def get_product_price_history(product_id):
    """Get price history for a specific product"""
    try:
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Product not found"}), 404
            
        # Get price history for each competitor
        query = """
        SELECT 
            pc.id AS crawl_id,
            e.name AS enemy_name,
            e.domain AS enemy_domain,
            pcl.price,
            pcl.timestamp
        FROM 
            product_crawl_logs pcl
        JOIN 
            product_crawls pc ON pcl.product_crawl_id = pc.id
        JOIN 
            enemies e ON pc.enemy_id = e.id
        WHERE 
            pc.prod_id = %s
        ORDER BY 
            e.name, pcl.timestamp DESC
        """
        
        cursor.execute(query, (product_id,))
        logs = cursor.fetchall()
        
        # Format prices and dates
        for log in logs:
            if log['price'] is not None:
                log['price'] = float(log['price'])
                log['formatted_price'] = f"{log['price']:,.0f} VND"
            log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Group by enemy
        price_history = {}
        for log in logs:
            enemy_name = log['enemy_name']
            if enemy_name not in price_history:
                price_history[enemy_name] = []
            price_history[enemy_name].append(log)
        
        cursor.close()
        
        return jsonify({"price_history": price_history})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get statistics for the dashboard"""
    try:
        connection = db.connection
        if not connection or not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Get total products count
        cursor.execute("SELECT COUNT(*) as count FROM products")
        total_products = cursor.fetchone()['count']
        
        # Get total enemies count
        cursor.execute("SELECT COUNT(*) as count FROM enemies")
        total_enemies = cursor.fetchone()['count']
        
        # Get total crawls count
        cursor.execute("SELECT COUNT(*) as count FROM product_crawls")
        total_crawls = cursor.fetchone()['count']
        
        # Get total crawl logs count
        cursor.execute("SELECT COUNT(*) as count FROM product_crawl_logs")
        total_logs = cursor.fetchone()['count']
        
        # Get products with the most competitor links
        cursor.execute("""
            SELECT 
                p.id, 
                p.name, 
                COUNT(pc.id) as competitor_count 
            FROM 
                products p
            LEFT JOIN 
                product_crawls pc ON p.id = pc.prod_id
            GROUP BY 
                p.id, p.name
            ORDER BY 
                competitor_count DESC
            LIMIT 5
        """)
        top_products = cursor.fetchall()
        
        # Get websites with the most products
        cursor.execute("""
            SELECT 
                e.name, 
                COUNT(pc.id) as product_count 
            FROM 
                enemies e
            LEFT JOIN 
                product_crawls pc ON e.id = pc.enemy_id
            GROUP BY 
                e.id, e.name
            ORDER BY 
                product_count DESC
            LIMIT 5
        """)
        top_websites = cursor.fetchall()
        
        # Get latest crawl logs
        cursor.execute("""
            SELECT 
                pcl.id,
                pcl.name as product_name,
                pcl.price,
                pcl.timestamp,
                e.name as website_name
            FROM 
                product_crawl_logs pcl
            JOIN 
                product_crawls pc ON pcl.product_crawl_id = pc.id
            JOIN 
                enemies e ON pc.enemy_id = e.id
            ORDER BY 
                pcl.timestamp DESC
            LIMIT 10
        """)
        latest_logs = cursor.fetchall()
        
        # Format prices
        for log in latest_logs:
            if log['price'] is not None:
                log['price'] = f"{log['price']:,.0f} VND"
            log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        
        return jsonify({
            "total_products": total_products,
            "total_enemies": total_enemies,
            "total_crawls": total_crawls,
            "total_logs": total_logs,
            "top_products": top_products,
            "top_websites": top_websites,
            "latest_logs": latest_logs
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/refresh', methods=['GET'])
def refresh_data():
    """Refresh all data (placeholder for any data refresh operations)"""
    try:
        # This would typically involve refreshing cached data or similar
        # For now, just return success
        return jsonify({"message": "Data refreshed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def clean_price(price_str):
    """Convert price string to float"""
    if not price_str or not isinstance(price_str, str):
        return None
    
    # Call the existing clean_price function from SaveToMSQL
    return db.clean_price(price_str)
    
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    # Log the error
    err.log_error(error, err.ErrorTypes.UNKNOWN)
    return jsonify({'error': 'Internal server error. The issue has been logged.'}), 500

@app.errorhandler(mysql.connector.Error)
def handle_database_error(error):
    # Use our error handler for database errors
    error_message = err.handle_database_error(error)
    return jsonify({'error': error_message}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Generic exception handler with improved logging
    error_details = err.log_error(e)
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({
        'error': 'An unexpected error occurred. The issue has been logged.',
        'error_id': error_details.get('timestamp', '')
    }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)