"""
Smart Attendance Desktop Application
Standalone desktop app using PyWebView
"""

import webview
import threading
import time
import sys
import os
from pathlib import Path

# Fix encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Paths
BASE_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = BASE_DIR / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

def start_flask():
    """Start Flask backend in background"""
    os.chdir(BACKEND_DIR)
    from app import app
    # Use 0.0.0.0 to ensure it binds properly
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False, threaded=True)

def main():
    print("=" * 60)
    print("  Smart Attendance Desktop Application")
    print("  Starting...")
    print("=" * 60)
    
    # Start Flask backend
    print("\n[*] Initializing backend server...")
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Wait for backend to be ready
    print("[*] Waiting for backend to initialize...")
    time.sleep(6)
    print("[+] Backend ready!\n")
    
    # Create PyWebView window
    print("[+] Opening application window...")
    
    window = webview.create_window(
        'Smart Attendance - FER System',
        'http://127.0.0.1:8000',
        width=1400,
        height=900,
        resizable=True,
        min_size=(1000, 700),
        background_color='#E8F4F8'
    )
    
    # Start PyWebView (blocking call)
    webview.start(debug=False)
    
    print("\n[*] Application closed.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[*] Application terminated by user.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
