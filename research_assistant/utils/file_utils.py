import os
import json
from typing import Any, Optional, Dict, List
from datetime import datetime

def save_json(data: Dict, file_path: str, indent: int = 2) -> bool:
    """
    Save dictionary data to a JSON file with error handling
    Returns True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving JSON to {file_path}: {str(e)}")
        return False

def load_json(file_path: str) -> Optional[Dict]:
    """Load JSON data from file with error handling"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading JSON from {file_path}: {str(e)}")
        return None

def save_text(content: str, file_path: str) -> bool:
    """Save text content to file with UTF-8 encoding"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except IOError as e:
        print(f"Error saving text to {file_path}: {str(e)}")
        return False

def load_text(file_path: str) -> Optional[str]:
    """Load text content from file with UTF-8 encoding"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        print(f"Error loading text from {file_path}: {str(e)}")
        return None

def create_timestamped_dir(base_path: str, prefix: str = "") -> str:
    """Create a timestamped directory and return its path"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{prefix}_{timestamp}" if prefix else timestamp
    dir_path = os.path.join(base_path, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path
