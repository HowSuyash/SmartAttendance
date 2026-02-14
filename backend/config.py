"""
Configuration module for Smart Attendance FER system.
Loads environment variables and provides configuration settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Hugging Face Configuration
    HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN', '')
    HUGGINGFACE_MODEL_URL = os.getenv(
        'HUGGINGFACE_MODEL_URL',
        'https://api-inference.huggingface.co/models/trpakov/vit-face-expression'
    )
    
    # Firebase Configuration
    _backend_dir = os.path.dirname(os.path.abspath(__file__))
    FIREBASE_CREDENTIALS_PATH = os.path.join(_backend_dir, 'firebase-credentials.json')
    
    # Flask Configuration
    FLASK_PORT = int(os.getenv('FLASK_PORT', 8000))
    FLASK_DEBUG = False  # Disabled to prevent reloader issues
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Emotion to Engagement Mapping
    ENGAGED_EMOTIONS = ['happy', 'surprise', 'neutral']
    DISENGAGED_EMOTIONS = ['sad', 'angry', 'fear', 'disgust']
    
    # Face Detection Configuration
    MIN_DETECTION_CONFIDENCE = 0.5
    MIN_FACE_SIZE = 20  # Minimum face size in pixels
    
    @staticmethod
    def validate():
        """Validate required configuration settings"""
        errors = []
        
        if not Config.HUGGINGFACE_API_TOKEN:
            errors.append("HUGGINGFACE_API_TOKEN is not set")
        
        if not os.path.exists(Config.FIREBASE_CREDENTIALS_PATH):
            errors.append(f"Firebase credentials file not found at {Config.FIREBASE_CREDENTIALS_PATH}")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))
        
        return True
