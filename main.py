#!/usr/bin/env python3
"""Main entry point for Android Multi-Emulator Manager"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gui.main_window import main

if __name__ == "__main__":
    main()
