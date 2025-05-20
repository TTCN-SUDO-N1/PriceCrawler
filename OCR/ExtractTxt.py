import google.generativeai as genai
from PIL import Image  # For opening image files
import os
from dotenv import load_dotenv
import json

load_dotenv()

def Extract(imgURL):
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
        return
    except Exception as e:
        print(f"Error loading image '{imgURL}': {e}")
        return

    model = genai.GenerativeModel(model_name)
    prompt_text = prompt_text_env
    if not prompt_text:
        print("Error: PROMPT_TEXT environment variable is not set.")
        return
    contents = [prompt_text, img]
    try:
        response = model.generate_content(contents)

        responseJson = PraseResponse(response.text)
    except Exception as e:
        return e
    return responseJson

def PraseResponse(response_string):
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
    except json.JSONDecodeError as e:
        print(f"Error parsing new product JSON from response: {e}")
        print(f"Problematic string snippet: {json_string[:200]}...")
        return
    return new_product_data