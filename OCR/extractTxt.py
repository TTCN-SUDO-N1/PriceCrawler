import google.generativeai as genai
from PIL import Image # For opening image files
import os
from dotenv import load_dotenv
import json
import datetime
load_dotenv()

def Extract(imgURL, store_name): # Added store_name back

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
        exit()

    try:
        img = Image.open(imgURL)
    except FileNotFoundError:
        print(f"Error: Image file '{imgURL}' not found. Please check the path.")
        return # Return instead of exit to allow processing other URLs
    except Exception as e:
        print(f"Error loading image '{imgURL}': {e}")
        return # Return instead of exit

    model = genai.GenerativeModel(model_name) # Or 'gemini-pro-vision'


    prompt_text = prompt_text_env
    if not prompt_text:
        print("Error: PROMPT_TEXT environment variable is not set.")
        return # Return instead of exit

    contents = [prompt_text, img]


    try:
        print(f"Sending request to Gemini API for {store_name} ({os.path.basename(imgURL)})...")
        response = model.generate_content(contents)
        print(f"Response received for {store_name}.")
        # print(response.text) # Optionally print the raw response

        # Define output filename based on store name
        output_filename = f"{store_name}.json"

        # Parse the response, update/create the JSON file
        PraseResponse(response.text, output_filename) # Pass imgURL for potential use inside PraseResponse if needed

    except Exception as e:
        print(f"\nAn error occurred during the API call or processing for {store_name}: {e}")


def PraseResponse(response_string, output_filename):

    # --- 1. Parse the new product data ---
    new_product_data = None
    # Remove Markdown code block fences if present
    if response_string.startswith("```json"):
        json_string = response_string.strip().replace("```json", "").replace("```", "").strip()
    elif response_string.startswith("```"):
         json_string = response_string.strip().replace("```", "").strip()
    else:
        json_string = response_string

    try:
        new_product_data = json.loads(json_string)
        now = datetime.datetime.now()
        new_product_data["timestamp"] = now.isoformat()
        
    except json.JSONDecodeError as e:
        print(f"Error parsing new product JSON from response: {e}")
        print(f"Problematic string snippet: {json_string[:200]}...")
        return # Stop processing if the new data is invalid

    # --- 2. Read existing data ---
    all_products_data = []
    if os.path.exists(output_filename):
        try:
            with open(output_filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    all_products_data = existing_data
                else:
                    print(f"Warning: Existing file '{output_filename}' does not contain a list. Overwriting with new data in a list.")
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from existing file '{output_filename}'. Starting fresh.")
        except IOError as e:
            print(f"Warning: Could not read existing file '{output_filename}': {e}. Starting fresh.")
    
    
    all_products_data.append(new_product_data)
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_products_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully updated and saved JSON data to '{output_filename}'")
    except IOError as e:
        print(f"Error writing updated JSON to file '{output_filename}': {e}")