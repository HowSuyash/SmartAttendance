"""
Face Detection module using MediaPipe.
Detects faces in images and extracts individual face regions.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from typing import List, Tuple, Dict
from config import Config


class FaceDetector:
    """Face detector using MediaPipe Face Detection"""
    
    def __init__(self, min_detection_confidence: float = None):
        """
        Initialize the face detector.
        
        Args:
            min_detection_confidence: Minimum confidence threshold for face detection
        """
        self.min_detection_confidence = min_detection_confidence or Config.MIN_DETECTION_CONFIDENCE
        
        # Create face detector with new API
        base_options = python.BaseOptions(model_asset_path='')
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=self.min_detection_confidence
        )
        
        # For now, use OpenCV's Haar Cascade as fallback since MediaPipe API changed
        self.use_opencv = True
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def detect_faces(self, image_path: str) -> Tuple[List[Dict], np.ndarray]:
        """
        Detect faces in an image and extract face regions.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Tuple of (list of face data dictionaries, original image array)
            Each face dictionary contains: bbox, face_image, confidence
        """
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image from {image_path}")
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using OpenCV Haar Cascade
        # scaleFactor: 1.05 is more thorough (smaller steps)
        # minNeighbors: 4 is less strict to catch more faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=4,
            minSize=(Config.MIN_FACE_SIZE, Config.MIN_FACE_SIZE),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        print(f"[OK] Face Detection: Found {len(faces)} face(s) in image")
        
        faces_data = []
        height, width, _ = image.shape
        
        for idx, (x, y, w, h) in enumerate(faces):
            # Ensure bbox is within image boundaries
            x = max(0, x)
            y = max(0, y)
            w = min(width - x, w)
            h = min(height - y, h)
            
            bbox = {
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h)
            }
            
            # Extract face region
            face_image = image[y:y+h, x:x+w]
            
            # Validate we have a valid face region
            if face_image.size == 0:
                print(f"  [!] Warning: Face {idx + 1} has invalid dimensions, skipping")
                continue
            
            # OpenCV doesn't provide confidence, use 0.9 as default
            confidence = 0.9
            
            print(f"  Face {idx + 1}: Position ({x}, {y}), Size {w}x{h}")
            
            faces_data.append({
                'bbox': bbox,
                'face_image': face_image,
                'confidence': float(confidence)
            })
        
        print(f"[OK] Validated {len(faces_data)} face(s) ready for analysis")
        return faces_data, image
    
    def draw_faces(self, image: np.ndarray, faces_data: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes around detected faces.
        
        Args:
            image: Original image array
            faces_data: List of face data dictionaries
            
        Returns:
            Image with drawn bounding boxes
        """
        annotated_image = image.copy()
        
        for face in faces_data:
            bbox = face['bbox']
            confidence = face['confidence']
            
            # Draw rectangle
            cv2.rectangle(
                annotated_image,
                (bbox['x'], bbox['y']),
                (bbox['x'] + bbox['width'], bbox['y'] + bbox['height']),
                (0, 255, 0),
                2
            )
            
            # Draw confidence score
            label = f"{confidence:.2f}"
            cv2.putText(
                annotated_image,
                label,
                (bbox['x'], bbox['y'] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        
        return annotated_image
