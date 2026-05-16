"""
Main entry point for the Crypto/Stock Price Tracker application.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui import main

if __name__ == "__main__":
    print("Starting Crypto/Stock Price Tracker...")
    main()
