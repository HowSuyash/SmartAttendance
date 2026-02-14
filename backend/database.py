"""
Firebase Firestore database integration.
Handles storage and retrieval of attendance analysis data.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, List, Optional
from config import Config


class Database:
    """Firebase Firestore database handler"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure single Firebase instance"""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase connection"""
        if not Database._initialized:
            try:
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                Database._initialized = True
            except Exception as e:
                raise Exception(f"Failed to initialize Firebase: {str(e)}")
    
    def create_session(self, metadata: Dict) -> str:
        """
        Create a new analysis session.
        
        Args:
            metadata: Session metadata (class_name, timestamp, etc.)
            
        Returns:
            Session ID
        """
        session_data = {
            'timestamp': datetime.utcnow(),
            'class_name': metadata.get('class_name', 'Unknown'),
            'image_name': metadata.get('image_name', 'Unknown'),
            'status': 'processing'
        }
        
        # Add session to Firestore
        doc_ref = self.db.collection('sessions').document()
        doc_ref.set(session_data)
        
        return doc_ref.id
    
    def save_analysis_results(self, session_id: str, analysis_results: List[Dict], stats: Dict):
        """
        Save analysis results to database.
        
        Args:
            session_id: Session ID
            analysis_results: List of individual face analysis results
            stats: Overall engagement statistics
        """
        # Update session with results
        session_ref = self.db.collection('sessions').document(session_id)
        session_ref.update({
            'status': 'completed',
            'completed_at': datetime.utcnow(),
            'statistics': stats
        })
        
        # Save individual face results
        batch = self.db.batch()
        faces_collection = session_ref.collection('faces')
        
        for result in analysis_results:
            face_ref = faces_collection.document()
            batch.set(face_ref, {
                **result,
                'timestamp': datetime.utcnow()
            })
        
        batch.commit()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data dictionary or None if not found
        """
        doc_ref = self.db.collection('sessions').document(session_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        
        return None
    
    def get_session_faces(self, session_id: str) -> List[Dict]:
        """
        Retrieve all face results for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of face analysis results
        """
        session_ref = self.db.collection('sessions').document(session_id)
        faces_ref = session_ref.collection('faces')
        
        faces = []
        for doc in faces_ref.stream():
            face_data = doc.to_dict()
            face_data['id'] = doc.id
            faces.append(face_data)
        
        return faces
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent analysis sessions.
        
        Args:
            limit: Maximum number of sessions to retrieve
            
        Returns:
            List of session data dictionaries
        """
        sessions_ref = self.db.collection('sessions').order_by(
            'timestamp', direction=firestore.Query.DESCENDING
        ).limit(limit)
        
        sessions = []
        for doc in sessions_ref.stream():
            session_data = doc.to_dict()
            session_data['id'] = doc.id
            sessions.append(session_data)
        
        return sessions
    
    def get_engagement_trends(self, days: int = 7) -> Dict:
        """
        Get engagement trends over specified number of days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        sessions_ref = self.db.collection('sessions').where(
            'timestamp', '>=', start_date
        ).where('status', '==', 'completed')
        
        daily_stats = {}
        
        for doc in sessions_ref.stream():
            session_data = doc.to_dict()
            date_key = session_data['timestamp'].strftime('%Y-%m-%d')
            
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'total_faces': 0,
                    'engaged': 0,
                    'disengaged': 0,
                    'sessions': 0
                }
            
            stats = session_data.get('statistics', {})
            daily_stats[date_key]['total_faces'] += stats.get('total_faces', 0)
            daily_stats[date_key]['engaged'] += stats.get('engaged_count', 0)
            daily_stats[date_key]['disengaged'] += stats.get('disengaged_count', 0)
            daily_stats[date_key]['sessions'] += 1
        
        return daily_stats
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all associated face data.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted successfully
        """
        try:
            session_ref = self.db.collection('sessions').document(session_id)
            
            # Delete all faces in the session
            faces_ref = session_ref.collection('faces')
            batch = self.db.batch()
            
            for doc in faces_ref.stream():
                batch.delete(doc.reference)
            
            batch.commit()
            
            # Delete the session document
            session_ref.delete()
            
            return True
        except Exception:
            return False
