import json
import logging
from typing import Any, Dict

# Оставляем существующие функции для обратной совместимости
def read_json_file(path: str, default_data=None):
    default_data = default_data or {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default_data
    except json.JSONDecodeError as e:
        logging.error(f"Error reading JSON from {path}: {e}")
        return default_data

def write_json_file(path: str, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Error writing JSON to {path}: {e}")