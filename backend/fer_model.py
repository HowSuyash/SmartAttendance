"""
Facial Expression Recognition module using Hugging Face Inference API.
Analyzes facial expressions and maps them to engagement levels.
"""

import requests
import cv2
import numpy as np
from typing import Dict, List
from io import BytesIO
from PIL import Image
from config import Config


class FERModel:
    """Facial Expression Recognition using Hugging Face API"""
    
    def __init__(self, api_token: str = None, model_url: str = None):
        """
        Initialize the FER model.
        
        Args:
            api_token: Hugging Face API token
            model_url: URL of the Hugging Face model endpoint
        """
        self.api_token = api_token or Config.HUGGINGFACE_API_TOKEN
        self.model_url = model_url or Config.HUGGINGFACE_MODEL_URL
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
    
    def predict_emotion(self, face_image: np.ndarray, max_retries: int = 3) -> Dict:
        """
        Predict emotion from a face image.
        
        Args:
            face_image: Face image as numpy array (BGR format from OpenCV)
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with emotion predictions and scores
        """
        # Convert BGR to RGB
        face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(face_rgb)
        
        # Convert to bytes
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
        
        # Make API request with retries
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.model_url,
                    headers=self.headers,
                    data=image_bytes,
                    timeout=10
                )
                
                if response.status_code == 200:
                    predictions = response.json()
                    return self._process_predictions(predictions)
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)
                        continue
                else:
                    raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    continue
                raise Exception("API request timeout")
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
                raise e
        
        raise Exception("Max retries exceeded")
    
    def _process_predictions(self, predictions: List[Dict]) -> Dict:
        """
        Process API predictions and extract top emotion.
        
        Args:
            predictions: List of prediction dictionaries from API
            
        Returns:
            Dictionary with emotion, score, and all predictions
        """
        if not predictions:
            return {
                'emotion': 'unknown',
                'score': 0.0,
                'all_predictions': []
            }
        
        # Sort by score
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)
        
        # Get top prediction
        top_prediction = sorted_predictions[0]
        
        return {
            'emotion': top_prediction['label'].lower(),
            'score': float(top_prediction['score']),
            'all_predictions': [
                {'label': p['label'].lower(), 'score': float(p['score'])}
                for p in sorted_predictions
            ]
        }
    
    def get_engagement_level(self, emotion: str) -> str:
        """
        Map emotion to engagement level.
        
        Args:
            emotion: Detected emotion (lowercase)
            
        Returns:
            Engagement level: 'engaged' or 'disengaged'
        """
        if emotion in Config.ENGAGED_EMOTIONS:
            return 'engaged'
        elif emotion in Config.DISENGAGED_EMOTIONS:
            return 'disengaged'
        else:
            return 'unknown'
    
    def analyze_faces(self, faces_data: List[Dict]) -> List[Dict]:
        """
        Analyze multiple faces and determine engagement levels.
        
        Args:
            faces_data: List of face data dictionaries from face detector
            
        Returns:
            List of analysis results with emotions and engagement levels
        """
        results = []
        
        for idx, face in enumerate(faces_data):
            try:
                print(f"Analyzing face {idx + 1}/{len(faces_data)}...")
                # Predict emotion
                emotion_result = self.predict_emotion(face['face_image'])
                print(f"  SUCCESS: Emotion: {emotion_result['emotion']} ({emotion_result['score']:.2f})")
                
                # Get engagement level
                engagement = self.get_engagement_level(emotion_result['emotion'])
                
                result = {
                    'face_id': idx,
                    'bbox': face['bbox'],
                    'detection_confidence': face['confidence'],
                    'emotion': emotion_result['emotion'],
                    'emotion_score': emotion_result['score'],
                    'engagement_level': engagement,
                    'all_emotions': emotion_result['all_predictions']
                }
                
                results.append(result)
                
            except Exception as e:
                # If emotion detection fails for a face, record error
                print(f"  ERROR analyzing face {idx + 1}: {str(e)}")
                results.append({
                    'face_id': idx,
                    'bbox': face['bbox'],
                    'detection_confidence': face['confidence'],
                    'emotion': 'error',
                    'emotion_score': 0.0,
                    'engagement_level': 'unknown',
                    'error': str(e)
                })
        
        return results
    
    def calculate_engagement_stats(self, analysis_results: List[Dict]) -> Dict:
        """
        Calculate overall engagement statistics.
        
        Args:
            analysis_results: List of analysis results
            
        Returns:
            Dictionary with engagement statistics
        """
        total_faces = len(analysis_results)
        
        print(f"\n[STATS] Calculating Statistics:")
        print(f"  Total faces detected: {total_faces}")
        
        if total_faces == 0:
            return {
                'total_faces': 0,
                'engaged_count': 0,
                'disengaged_count': 0,
                'unknown_count': 0,
                'engagement_percentage': 0.0,
                'emotion_distribution': {}
            }
        
        engaged_count = sum(1 for r in analysis_results if r['engagement_level'] == 'engaged')
        disengaged_count = sum(1 for r in analysis_results if r['engagement_level'] == 'disengaged')
        unknown_count = sum(1 for r in analysis_results if r['engagement_level'] == 'unknown')
        
        print(f"  Engaged students: {engaged_count}")
        print(f"  Disengaged students: {disengaged_count}")
        print(f"  Unknown status: {unknown_count}")
        
        # Validation: ensure counts add up
        total_check = engaged_count + disengaged_count + unknown_count
        if total_check != total_faces:
            print(f"  [!] WARNING: Count mismatch! {total_check} vs {total_faces}")
        
        # Count emotions
        emotion_counts = {}
        for result in analysis_results:
            emotion = result['emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        engagement_percentage = (engaged_count / total_faces * 100) if total_faces > 0 else 0.0
        print(f"  Engagement rate: {engagement_percentage:.1f}%")
        print(f"  Emotion breakdown: {emotion_counts}\n")
        
        return {
            'total_faces': total_faces,
            'engaged_count': engaged_count,
            'disengaged_count': disengaged_count,
            'unknown_count': unknown_count,
            'engagement_percentage': engagement_percentage,
            'emotion_distribution': emotion_counts
        }
