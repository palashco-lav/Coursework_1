from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

def export_to_file(func):
    def wrapper(*args, **kwargs):
        file_path = f"{BASE_DIR}/report.txt"
        result = func(*args, **kwargs)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(str(result))
        return result
    return wrapper

def export_to_file_with_name(filename):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(str(result))
            return result
        return wrapper
    return decorator
