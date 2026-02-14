"""
Authentication module for Smart Attendance system.
Handles user registration, login, and session management.
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from firebase_admin import firestore

# Secret key for JWT (in production, use environment variable)
JWT_SECRET = "smart_attendance_secret_key_change_in_production"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


class AuthManager:
    """Manages authentication and user sessions"""
    
    def __init__(self, db):
        """
        Initialize auth manager.
        
        Args:
            db: Firestore database instance
        """
        self.db = db
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_token(self, user_id: str, role: str) -> str:
        """
        Generate JWT token for authenticated user.
        
        Args:
            user_id: User's unique ID
            role: User role (student or institution)
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            print("Token expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")
            return None
    
    def signup_institution(self, email: str, password: str, institution_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new institution account.
        
        Args:
            email: Institution email
            password: Password
            institution_name: Name of institution
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Check if email already exists
            users_ref = self.db.collection('users')
            existing = users_ref.where('email', '==', email).limit(1).get()
            
            if len(list(existing)) > 0:
                return False, "Email already registered", None
            
            # Create user document
            user_data = {
                'email': email,
                'password_hash': self.hash_password(password),
                'role': 'institution',
                'institution_name': institution_name,
                'created_at': firestore.SERVER_TIMESTAMP,
                'active': True
            }
            
            # Add to database
            doc_ref = users_ref.add(user_data)
            user_id = doc_ref[1].id
            
            # Generate token
            token = self.generate_token(user_id, 'institution')
            
            return True, "Institution registered successfully", {
                'user_id': user_id,
                'email': email,
                'role': 'institution',
                'institution_name': institution_name,
                'token': token
            }
            
        except Exception as e:
            print(f"Signup error: {e}")
            return False, f"Registration failed: {str(e)}", None
    
    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user login.
        
        Args:
            email: User email
            password: Password
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Find user by email
            users_ref = self.db.collection('users')
            users = users_ref.where('email', '==', email).limit(1).get()
            
            user_list = list(users)
            if len(user_list) == 0:
                return False, "Invalid email or password", None
            
            user_doc = user_list[0]
            user_data = user_doc.to_dict()
            user_id = user_doc.id
            
            # Verify password
            password_hash = self.hash_password(password)
            if password_hash != user_data.get('password_hash'):
                return False, "Invalid email or password", None
            
            # Check if account is active
            if not user_data.get('active', True):
                return False, "Account is deactivated", None
            
            # Generate token
            token = self.generate_token(user_id, user_data['role'])
            
            return True, "Login successful", {
                'user_id': user_id,
                'email': user_data['email'],
                'role': user_data['role'],
                'institution_name': user_data.get('institution_name'),
                'student_name': user_data.get('student_name'),
                'token': token
            }
            
        except Exception as e:
            print(f"Login error: {e}")
            return False, f"Login failed: {str(e)}", None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user information by ID.
        
        Args:
            user_id: User's unique ID
            
        Returns:
            User data or None
        """
        try:
            doc = self.db.collection('users').document(user_id).get()
            if doc.exists:
                data = doc.to_dict()
                # Remove password hash from response
                data.pop('password_hash', None)
                data['user_id'] = user_id
                return data
            return None
        except Exception as e:
            print(f"Get user error: {e}")
            return None
    
    def create_student(self, institution_id: str, student_name: str, student_number: str, email: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Create a student account linked to an institution.
        
        Args:
            institution_id: ID of the institution
            student_name: Student's full name
            student_number: Student number/ID
            email: Optional student email
            
        Returns:
            Tuple of (success, message, student_id)
        """
        try:
            # Check if student number already exists for this institution
            students_ref = self.db.collection('students')
            existing = students_ref.where('institution_id', '==', institution_id)\
                                   .where('student_number', '==', student_number)\
                                   .limit(1).get()
            
            if len(list(existing)) > 0:
                return False, "Student number already exists", None
            
            # Create student document
            student_data = {
                'institution_id': institution_id,
                'student_name': student_name,
                'student_number': student_number,
                'email': email,
                'created_at': firestore.SERVER_TIMESTAMP,
                'active': True
            }
            
            doc_ref = students_ref.add(student_data)
            student_id = doc_ref[1].id
            
            return True, "Student created successfully", student_id
            
        except Exception as e:
            print(f"Create student error: {e}")
            return False, f"Failed to create student: {str(e)}", None
