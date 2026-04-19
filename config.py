from dotenv import load_dotenv
import os

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_TOKEN = os.getenv("API_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
DATA_PATH = os.getenv("DATA_PATH")