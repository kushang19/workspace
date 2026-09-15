"""File-system tools used by the React agent."""

from pathlib import Path
from agent.events import emit_event

def write_file(file_path: str, content: str):
    """
    Write content to a file. Creates directories if needed.
    
    Parameters:
    - file_path: The path where the file should be created
    - content: The content to write to the file
    """
    try:
        # Create parent directories if they don't exist
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "file_path": file_path,
            "message": f"File created successfully: {file_path}"
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }

def read_file(file_path: str):
    """
    Read content from a file.
    
    Parameters:
    - file_path: The path of the file to read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_path": file_path
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }

def list_directory(directory_path: str):
    """
    List contents of a directory.
    
    Parameters:
    - directory_path: The path of the directory to list
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory_path}"
            }
        
        items = []
        for item in path.iterdir():
            items.append({
                "name": item.name,
                "is_directory": item.is_dir(),
                "path": str(item)
            })
        
        return {
            "success": True,
            "items": items,
            "directory": directory_path
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }
