import os
from dotenv import load_dotenv

# Load from the FinApp root directory .env.local
load_dotenv(dotenv_path='../.env.local')
# Fallback if not found
if not os.environ.get('MONGODB_URI'):
    load_dotenv(dotenv_path='../.env')

MONGODB_URI = os.environ.get('MONGODB_URI')

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in environment variables.")
