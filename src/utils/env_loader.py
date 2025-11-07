"""
Environment Variable Loader Utility

This module provides a utility function to load environment variables
from the .env file in the iteration1 folder.
"""

from pathlib import Path
from typing import Optional


def load_iteration1_env() -> Optional[Path]:
    """
    Load environment variables from .env file in iteration1 folder.
    
    This function looks for a .env file in the iteration1 folder,
    which is 2 levels up from any file in iteration1/src/.
    
    Returns:
        Path to the .env file if found and loaded, None otherwise
        
    Example:
        >>> env_path = load_iteration1_env()
        >>> if env_path:
        ...     print(f"Loaded .env from {env_path}")
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        # python-dotenv not installed
        return None
    
    # Calculate path to iteration1/.env
    # This file is at: iteration1/src/utils/env_loader.py
    # .env is at: iteration1/.env (2 levels up: utils -> src -> iteration1)
    current_file = Path(__file__)
    env_path = current_file.parent.parent.parent / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        return env_path
    
    return None

