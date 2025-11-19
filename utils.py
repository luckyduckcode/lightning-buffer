import os
import re
from datetime import datetime
from config import AUTOMATIONS_HOST_DIR, MAX_FILENAME_LENGTH

def generate_safe_filename(prompt: str) -> str:
    """
    Generates a safe filename from a prompt with a timestamp.
    Example: "make a backup script" -> "make_a_backup_script_2023-10-27_10-30.py"
    """
    # Clean prompt: keep only alphanumeric and spaces
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ]', '', prompt)
    # Replace spaces with underscores
    clean_prompt = clean_prompt.replace(' ', '_').lower()
    # Truncate
    clean_prompt = clean_prompt[:50]
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{clean_prompt}_{timestamp}.py"
    return filename

def validate_and_join_path(filename: str) -> str:
    """
    Validates that the filename is safe (no traversal) and joins it with the host dir.
    Returns the full absolute path.
    Raises ValueError if invalid.
    """
    # Basic path traversal check
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename: path traversal detected")
    
    full_path = os.path.join(AUTOMATIONS_HOST_DIR, filename)
    return full_path

def get_container_path(filename: str) -> str:
    """
    Converts a filename to the path inside the Docker container.
    Assumes the container mounts AUTOMATIONS_HOST_DIR to /automations
    """
    return f"/automations/{filename}"
