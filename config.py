import os
from dotenv import load_dotenv

load_dotenv()

AUTOMATION_API_URL = os.getenv("AUTOMATION_API_URL", "http://localhost:3000")
AUTOMATION_API_KEY = os.getenv("AUTOMATION_API_KEY", "")
AUTOMATIONS_HOST_DIR = os.getenv("AUTOMATIONS_HOST_DIR", r"D:\AI-Automations")
BUFFER_PORT = int(os.getenv("BUFFER_PORT", 8000))
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-coder:6.7b")
MAX_FILENAME_LENGTH = int(os.getenv("MAX_FILENAME_LENGTH", 100))
