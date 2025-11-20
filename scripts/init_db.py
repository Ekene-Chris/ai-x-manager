#!/usr/bin/env python3
"""Initialize the database and create tables"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db
from app.config import settings

def main():
    """Initialize database"""
    print(f"Initializing database: {settings.database_url}")

    try:
        init_db()
        print("✓ Database initialized successfully!")
        print("✓ All tables created")
        return 0
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
