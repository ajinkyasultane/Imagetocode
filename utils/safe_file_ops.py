from __future__ import annotations
import os
import shutil
import stat
import time
from pathlib import Path
from typing import Optional

def handle_remove_readonly(func, path, exc):
    """Error handler for Windows readonly files."""
    if os.path.exists(path):
        # Make the file writable and try again
        os.chmod(path, stat.S_IWRITE)
        func(path)

def safe_rmtree(path: Path, max_retries: int = 3, delay: float = 0.5) -> bool:
    """
    Safely remove a directory tree, handling Windows permission issues.
    
    Args:
        path: Path to directory to remove
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        True if successful, False otherwise
    """
    if not path.exists():
        return True
        
    for attempt in range(max_retries):
        try:
            if os.name == 'nt':  # Windows
                # Use onerror handler for Windows readonly files
                shutil.rmtree(str(path), onerror=handle_remove_readonly)
            else:
                shutil.rmtree(str(path))
            return True
            
        except PermissionError as e:
            if attempt < max_retries - 1:
                # Wait and try again
                time.sleep(delay)
                
                # Try to make all files writable
                try:
                    for root, dirs, files in os.walk(str(path)):
                        for d in dirs:
                            dir_path = os.path.join(root, d)
                            try:
                                os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                            except:
                                pass
                        for f in files:
                            file_path = os.path.join(root, f)
                            try:
                                os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                            except:
                                pass
                except:
                    pass
                continue
            else:
                print(f"Warning: Could not remove directory {path} after {max_retries} attempts: {e}")
                return False
                
        except Exception as e:
            print(f"Warning: Unexpected error removing directory {path}: {e}")
            return False
    
    return False

def safe_mkdir(path: Path, parents: bool = True, exist_ok: bool = True) -> bool:
    """
    Safely create a directory, handling permission issues.
    
    Args:
        path: Path to directory to create
        parents: Create parent directories if needed
        exist_ok: Don't raise error if directory already exists
        
    Returns:
        True if successful, False otherwise
    """
    try:
        path.mkdir(parents=parents, exist_ok=exist_ok)
        return True
    except Exception as e:
        print(f"Warning: Could not create directory {path}: {e}")
        return False

def cleanup_temp_files(directory: Path) -> None:
    """Clean up temporary files that might cause permission issues."""
    if not directory.exists():
        return
        
    temp_patterns = [
        "*.tmp", "*.temp", "*.lock", "*.pid",
        ".DS_Store", "Thumbs.db", "desktop.ini"
    ]
    
    for pattern in temp_patterns:
        for temp_file in directory.rglob(pattern):
            try:
                if temp_file.is_file():
                    temp_file.chmod(stat.S_IWRITE)
                    temp_file.unlink()
            except:
                pass  # Ignore errors for temp file cleanup
