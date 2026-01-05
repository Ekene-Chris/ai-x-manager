
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    print("Importing app.main...")
    from app import main
    print("Import successful!")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
