"""
Smart Attendance - Simple Launcher
Starts the Flask backend and opens in default browser
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

def main():
    print("="*60)
    print("  Smart Attendance - FER System Launcher")
    print("="*60)
    
    # Get paths
    base_dir = Path(__file__).parent
    backend_dir = base_dir / 'backend'
    
    print("\n[1/2] Starting Flask backend server...")
    
    # Start Flask backend in background
    flask_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=str(backend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    
    # Wait for backend to start
    print("[*] Waiting for backend to initialize...")
    time.sleep(5)
    
    print("[2/2] Opening in browser...")
    url = "http://localhost:5001"
    
    # Open in default browser
    webbrowser.open(url)
    
    print(f"\n✓ Application opened in browser!")
    print(f"✓ URL: {url}")
    print(f"\nBackend server is running in a separate window.")
    print("Press Ctrl+C in that window to stop the server.\n")
    print("THIS WINDOW CAN NOW BE CLOSED.")
    
    input("\nPress Enter to exit launcher...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nLauncher closed")
    except Exception as e:
        print(f"\nError: {e}")
        input("\nPress Enter to exit...")
