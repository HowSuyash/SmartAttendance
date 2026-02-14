"""Simple Flask server runner"""
import sys
import os

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import and run app
from app import app

if __name__ == '__main__':
    print("="*60)
    print("  Smart Attendance Server")
    print("="*60)
    print("\nStarting on http://localhost:5001")
    print("Press Ctrl+C to stop\n")
    
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=False,
        threaded=True,
        use_reloader=False
    )
