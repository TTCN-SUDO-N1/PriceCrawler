import os
from dotenv import load_dotenv
load_dotenv()

api = os.getenv("GOOGLE_API_KEY")
print("API Key:", api)

