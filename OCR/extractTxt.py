import google.generativeai as genai
from PIL import Image # For opening image files
import os
from dotenv import load_dotenv
import json
import re  # Import for regular expressions

import SaveToMSQL as stsql
load_dotenv()

def Extract(imgURL, link, enemyOrOriginal, enemyName=None, enemyDomain=None):
    """
    Extract product information from screenshot using AI vision model
    
    Args:
        imgURL: Path to the screenshot image
        link: Original URL that was crawled
        enemyOrOriginal: 'enemy' for competitor product, 'original' for our own product
        enemyName: Name of the competitor (website name)
        enemyDomain: Domain of the competitor
    """
    # Import the database connection
    connection = stsql.connection

    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        model_name = os.getenv("GEMINI_MODEL")
        prompt_text_env = os.getenv("PROMPT_TEXT")
        if not api_key:
            raise ValueError("API key not found in environment variables")
        genai.configure(api_key=api_key)

    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the GOOGLE_API_KEY environment variable or configure the key directly.")
        return None  # Return instead of exit to allow processing other URLs

    try:
        img = Image.open(imgURL)
    except FileNotFoundError:
        print(f"Error: Image file '{imgURL}' not found. Please check the path.")
        return None
    except Exception as e:
        print(f"Error loading image '{imgURL}': {e}")
        return None

    model = genai.GenerativeModel(model_name) # Or 'gemini-pro-vision'

    prompt_text = prompt_text_env
    if not prompt_text:
        print("Error: PROMPT_TEXT environment variable is not set.")
        return None

    contents = [prompt_text, img]

    try:
        response = model.generate_content(contents)
        
        # Log the raw response for debugging
        print(f"Raw AI response (preview): {response.text[:100]}...")
        
        # Parse the response into structured data
        parsed_responses = ParseResponse(response.text, link)
        
        # Log what we got after parsing
        if isinstance(parsed_responses, list):
            print(f"Parsed {len(parsed_responses)} products")
        elif isinstance(parsed_responses, dict):
            print(f"Parsed a single product: {parsed_responses.get('product_name', 'Unknown')}")
        else:
            print(f"Unexpected parsed response type: {type(parsed_responses)}")
            # Convert to a compatible format
            parsed_responses = {
                "product_name": "Unknown Product",
                "link": link,
                "current_price": "",
                "raw_data": str(parsed_responses)
            }
            
        if enemyOrOriginal == 'enemy':
            # Save enemy info first
            enemy_id = stsql.save_enemy(enemyName, enemyDomain)
            print(f"Updated enemy: {enemyName} ({enemyDomain})")
            
            if enemy_id and connection:
                cursor = connection.cursor()
                
                # Get product name from parsed response for matching
                product_name = None
                if isinstance(parsed_responses, list) and len(parsed_responses) > 0:
                    product_name = parsed_responses[0].get('product_name', '')
                elif isinstance(parsed_responses, dict):
                    product_name = parsed_responses.get('product_name', '')
                
                if product_name:
                    print(f"Found product: '{product_name}' - Adding to database")
                    
                    # Skip the matching logic since we're adding all products to the database
                    # Extract values for the new product
                    current_price_str = ''
                    if isinstance(parsed_responses, dict):
                        current_price_str = parsed_responses.get('current_price', '')
                    elif isinstance(parsed_responses, list) and len(parsed_responses) > 0:
                        current_price_str = parsed_responses[0].get('current_price', '')
                    
                    # Clean the price using the function from SaveToMSQL
                    from SaveToMSQL import clean_price
                    price = clean_price(current_price_str)
                    
                    # Insert the new product
                    cursor.execute(
                        "INSERT INTO products (name, link, org_price, cur_price) VALUES (%s, %s, %s, %s)",
                        (product_name, link, price, price)
                    )
                    connection.commit()
                    new_product_id = cursor.lastrowid
                    
                    if new_product_id:
                        print(f"Created new product: {product_name} (ID: {new_product_id})")
                        # Create the crawl relationship
                        crawl_id = stsql.save_product_crawl(new_product_id, enemy_id, link)
                        
                        # Save the crawl log
                        if crawl_id:
                            log_ids = stsql.save_product_crawl_log(crawl_id, parsed_responses)
                            print(f"Saved {len(log_ids) if isinstance(log_ids, list) else 1} crawl log entries for new product")
                    else:
                        print("Failed to create new product")
                    
                    # Close the cursor
                    cursor.close()
                else:
                    print("No product name found in parsed response")
            else:
                print("Failed to save enemy information or database connection issue")
                
        elif enemyOrOriginal == 'original':
            # Save the original product
            stsql.save_originals(parsed_responses)
        
        return parsed_responses
    
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return None


def ParseResponse(response_string, link):
    print(f"Parsing response for link: {link}")
    print(f"Response text preview: {response_string[:100]}...")
    
    # Clean up the response string
    if response_string.startswith("```json"):
        json_string = response_string.strip().replace("```json", "").replace("```", "").strip()
    elif response_string.startswith("```"):
        json_string = response_string.strip().replace("```", "").strip()
    else:
        json_string = response_string.strip()
    
    # Try to parse the JSON string
    try:
        parsed_data = json.loads(json_string)
        
        # Add the link to the JSON data
        if isinstance(parsed_data, list):
            # Handle list of objects
            for item in parsed_data:
                item["link"] = link
        elif isinstance(parsed_data, dict):
            # Handle single object
            parsed_data["link"] = link
            
            # Check if this is a product object - verify it has required fields
            if not parsed_data.get('product_name'):
                # Try to intelligently extract a product name
                if 'name' in parsed_data:
                    parsed_data['product_name'] = parsed_data['name']
                elif 'title' in parsed_data:
                    parsed_data['product_name'] = parsed_data['title']
                # If we have phone name pattern in any field, use that
                elif any('iphone' in str(v).lower() or 'điện thoại' in str(v).lower() for v in parsed_data.values()):
                    for key, value in parsed_data.items():
                        if isinstance(value, str) and ('iphone' in value.lower() or 'điện thoại' in value.lower()):
                            parsed_data['product_name'] = value
                            break
                
            # Standardize price fields
            if not parsed_data.get('current_price') and not parsed_data.get('promotional_price'):
                for key, value in parsed_data.items():
                    if 'price' in key.lower() or 'giá' in key.lower():
                        if not parsed_data.get('current_price'):
                            parsed_data['current_price'] = value
                        elif not parsed_data.get('promotional_price'):
                            parsed_data['promotional_price'] = value
        else:
            # Unexpected data type - create a simple product structure
            parsed_data = {
                "product_name": "Unknown Product",
                "link": link,
                "current_price": "",
                "promotional_price": "",
                "raw_data": str(parsed_data)
            }
        
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"JSON string preview: {json_string[:200]}...")
        
        # Create a fallback product structure when JSON parsing fails
        # Try to extract product name from the text using simple pattern matching
        product_name = "Unknown Product"
        lines = response_string.split('\n')
        for line in lines:
            if 'name' in line.lower() or 'product' in line.lower() or 'sản phẩm' in line.lower() or 'tên' in line.lower():
                # Extract text after colon or similar separator
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    product_name = parts[1].strip().strip('"').strip("'")
                    break
            elif 'iphone' in line.lower() or 'điện thoại' in line.lower():
                product_name = line.strip()
                break
        
        # Try to extract price using similar pattern matching
        current_price = ""
        for line in lines:
            if 'price' in line.lower() or 'giá' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    current_price = parts[1].strip().strip('"').strip("'")
                    break
        
        return {
            "product_name": product_name,
            "link": link,
            "current_price": current_price,
            "promotional_price": "",
            "raw_text": response_string[:500]  # Store a preview of the raw response
        }



