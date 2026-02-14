"""
Flask API server for Smart Attendance FER system.
Provides endpoints for image upload, analysis, and results retrieval.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import cv2
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

from config import Config
from face_detector import FaceDetector
from fer_model import FERModel
from database import Database
from auth import AuthManager

# Initialize Flask app with static folder for frontend
app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

# Enable CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
})

# Disable caching to prevent PyWebView cache issues
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Create upload folder if it doesn't exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Initialize components
face_detector = FaceDetector()
fer_model = FERModel()
database = Database()
auth_manager = AuthManager(database.db)

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/')
def index():
    """Serve login page"""
    return app.send_static_file('login.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Upload and analyze classroom image.
    Expects: multipart/form-data with 'image' file and optional 'class_name'
    Returns: Analysis results with session_id
    """
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG'}), 400
        
        # Get optional metadata
        class_name = request.form.get('class_name', 'Unknown Class')
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # Create database session
        session_id = database.create_session({
            'class_name': class_name,
            'image_name': filename
        })
        
        # Perform analysis
        try:
            # 1. Detect faces
            faces_data, original_image = face_detector.detect_faces(filepath)
            
            if not faces_data:
                database.save_analysis_results(session_id, [], {
                    'total_faces': 0,
                    'engaged_count': 0,
                    'disengaged_count': 0,
                    'unknown_count': 0,
                    'engagement_percentage': 0.0,
                    'emotion_distribution': {}
                })
                return jsonify({
                    'session_id': session_id,
                    'message': 'No faces detected in the image',
                    'faces': [],
                    'statistics': {
                        'total_faces': 0,
                        'engaged_count': 0,
                        'disengaged_count': 0,
                        'engagement_percentage': 0.0
                    }
                }), 200
            
            # 2. Analyze emotions
            analysis_results = fer_model.analyze_faces(faces_data)
            
            # 3. Calculate statistics
            stats = fer_model.calculate_engagement_stats(analysis_results)
            
            # 4. Save to database
            database.save_analysis_results(session_id, analysis_results, stats)
            
            # 5. Save annotated image
            annotated_image = face_detector.draw_faces(original_image, faces_data)
            annotated_path = os.path.join(Config.UPLOAD_FOLDER, f"annotated_{unique_filename}")
            cv2.imwrite(annotated_path, annotated_image)
            
            return jsonify({
                'session_id': session_id,
                'message': 'Analysis completed successfully',
                'faces': analysis_results,
                'statistics': stats,
                'original_image': unique_filename,
                'annotated_image': f"annotated_{unique_filename}"
            }), 200
        
        except Exception as e:
            return jsonify({
                'error': f'Analysis failed: {str(e)}',
                'session_id': session_id
            }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    Retrieve session data and results.
    Returns: Session metadata and analysis results
    """
    try:
        session = database.get_session(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        faces = database.get_session_faces(session_id)
        
        return jsonify({
            'session': session,
            'faces': faces
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/sessions/recent', methods=['GET'])
def get_recent_sessions():
    """
    Get recent analysis sessions.
    Query params: limit (default: 10)
    """
    try:
        limit = int(request.args.get('limit', 10))
        sessions = database.get_recent_sessions(limit)
        
        return jsonify({
            'sessions': sessions,
            'count': len(sessions)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Get dashboard statistics.
    Query params: days (default: 7)
    """
    try:
        days = int(request.args.get('days', 7))
        trends_dict = database.get_engagement_trends(days)
        recent_sessions = database.get_recent_sessions(5)
        
        # Calculate overall statistics
        total_sessions = 0
        total_students = 0
        total_engaged = 0
        total_faces = 0
        
        # Get all sessions to calculate totals
        all_sessions = database.get_recent_sessions(100)  # Get more sessions for stats
        
        for session in all_sessions:
            stats = session.get('statistics', {})
            if stats:
                total_sessions += 1
                total_students += stats.get('total_faces', 0)
                total_engaged += stats.get('engaged_count', 0)
                total_faces += stats.get('total_faces', 0)
        
        # Calculate engagement percentage
        engagement_percentage = (total_engaged / total_faces * 100) if total_faces > 0 else 0
        
        # Format trends for chart
        trends = []
        for date_key, data in sorted(trends_dict.items()):
            trends.append({
                'date': date_key,
                'total': data['total_faces'],
                'engaged': data['engaged'],
                'disengaged': data['disengaged']
            })
        
        return jsonify({
            'total_sessions': total_sessions,
            'total_students': total_students,
            'engagement_percentage': engagement_percentage,
            'trends': trends,
            'recent_sessions': recent_sessions
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    """Serve uploaded images"""
    try:
        filepath = os.path.join(Config.UPLOAD_FOLDER, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Image not found'}), 404
        
        return send_file(filepath, mimetype='image/jpeg')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session and its associated data"""
    try:
        success = database.delete_session(session_id)
        
        if success:
            return jsonify({'message': 'Session deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete session'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large. Maximum size is 16MB'
    }), 413


# ========== Authentication Endpoints ==========

@app.route('/auth/signup', methods=['POST'])
def signup():
    """Register new institution"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        institution_name = data.get('institution_name')
        
        if not all([email, password, institution_name]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        success, message, user_data = auth_manager.signup_institution(email, password, institution_name)
        
        if success:
            return jsonify({'message': message, 'user': user_data}), 201
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Missing email or password'}), 400
        
        success, message, user_data = auth_manager.login(email, password)
        
        if success:
            return jsonify({'message': message, 'user': user_data}), 200
        else:
            return jsonify({'error': message}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/auth/me', methods=['GET'])
def get_current_user():
    """Get current user info from token"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
        
        token = auth_header.split(' ')[1]
        payload = auth_manager.verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        user_data = auth_manager.get_user_by_id(payload['user_id'])
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== Error Handlers ==========
def internal_server_error(error):
    """Handle internal server errors"""
    return jsonify({
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Validate configuration before starting
    try:
        # Note: Validation will be skipped if credentials are not yet set up
        # The app will fail when trying to use the services
        print("Starting Smart Attendance FER Server...")
        print(f"Server running on http://localhost:{Config.FLASK_PORT}")
        print(f"Upload folder: {Config.UPLOAD_FOLDER}")
        
        app.run(
            host='127.0.0.1',
            port=Config.FLASK_PORT,
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
