"""
Emotion Detection Module
Detects emotions from facial expressions using computer vision
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import os

@dataclass
class EmotionResult:
    """Result of emotion detection"""
    emotion: str
    confidence: float
    all_scores: Dict[str, float]
    timestamp: datetime
    smoothed: bool = False

class DetectionError(Exception):
    """Raised when emotion detection fails"""
    pass

class EmotionDetector:
    """Detects emotions from facial expressions"""
    
    EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
    
    def __init__(self, config):
        self.config = config
        emotion_config = config.get('emotion_detection', {})
        
        self.model_path = emotion_config.get('model_path', 'models/emotion_model.xml')
        self.confidence_threshold = emotion_config.get('confidence_threshold', 0.5)
        self.smoothing_frames = emotion_config.get('smoothing_frames', 3)
        
        # Frame buffer for temporal smoothing
        self.frame_buffer: List[EmotionResult] = []
        
        # Load emotion detection model
        self.model = self._load_model()
        
    def _load_model(self):
        """Load emotion detection model with error handling"""
        # For now, we'll use a simple heuristic-based approach
        # In production, you would load a trained model (e.g., from OpenCV DNN or TensorFlow)
        # This allows the system to work without requiring model files
        
        if os.path.exists(self.model_path):
            try:
                # Attempt to load model if available
                # model = cv2.dnn.readNet(self.model_path)
                # return model
                pass
            except Exception as e:
                print(f"Warning: Could not load emotion model from {self.model_path}: {e}")
        
        # Return None to indicate fallback mode
        return None
    
    def detect_emotion(self, frame, face_region=None) -> EmotionResult:
        """
        Detect emotion from a frame
        
        Args:
            frame: BGR image frame from camera
            face_region: Optional tuple (x, y, w, h) of face location
            
        Returns:
            EmotionResult with detected emotion and confidence
            
        Raises:
            DetectionError: If frame is invalid
        """
        if frame is None or frame.size == 0:
            raise DetectionError("Invalid frame data")
        
        try:
            # If no face region provided, detect it
            if face_region is None:
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) == 0:
                    # No face detected - return neutral with low confidence
                    return EmotionResult(
                        emotion='neutral',
                        confidence=0.5,
                        all_scores={'neutral': 0.5},
                        timestamp=datetime.now(),
                        smoothed=False
                    )
                
                face_region = faces[0]  # Use first detected face
            
            # Extract face region
            x, y, w, h = face_region
            face = frame[y:y+h, x:x+w]
            
            # Preprocess face for model
            face_processed = self._preprocess_face(face)
            
            # Run emotion detection
            if self.model is not None:
                # Use trained model
                emotion_scores = self._run_model_inference(face_processed)
            else:
                # Use heuristic fallback
                emotion_scores = self._heuristic_emotion_detection(face_processed)
            
            # Get dominant emotion
            emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[emotion]
            
            return EmotionResult(
                emotion=emotion,
                confidence=confidence,
                all_scores=emotion_scores,
                timestamp=datetime.now(),
                smoothed=False
            )
            
        except Exception as e:
            # On any error, return neutral with low confidence
            return EmotionResult(
                emotion='neutral',
                confidence=0.5,
                all_scores={'neutral': 0.5},
                timestamp=datetime.now(),
                smoothed=False
            )
    
    def _preprocess_face(self, face):
        """Preprocess face region for model input"""
        # Resize to standard size
        face_resized = cv2.resize(face, (48, 48))
        
        # Convert to grayscale
        if len(face_resized.shape) == 3:
            face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        else:
            face_gray = face_resized
        
        # Normalize
        face_normalized = face_gray / 255.0
        
        return face_normalized
    
    def _run_model_inference(self, face_processed):
        """Run inference using trained model"""
        # Placeholder for actual model inference
        # In production, this would use the loaded model
        # For now, fall back to heuristic
        return self._heuristic_emotion_detection(face_processed)
    
    def _heuristic_emotion_detection(self, face_processed):
        """
        Simple heuristic-based emotion detection
        This is a fallback when no trained model is available
        """
        # Calculate basic image statistics
        mean_intensity = np.mean(face_processed)
        std_intensity = np.std(face_processed)
        
        # Simple heuristic: use image statistics to estimate emotion
        # This is very basic and should be replaced with a real model
        scores = {
            'neutral': 0.4,
            'happy': 0.15,
            'sad': 0.15,
            'angry': 0.1,
            'surprise': 0.1,
            'fear': 0.05,
            'disgust': 0.05
        }
        
        # Adjust based on brightness (very rough heuristic)
        if mean_intensity > 0.6:
            scores['happy'] += 0.2
            scores['neutral'] -= 0.1
        elif mean_intensity < 0.4:
            scores['sad'] += 0.2
            scores['neutral'] -= 0.1
        
        # Normalize scores
        total = sum(scores.values())
        scores = {k: v/total for k, v in scores.items()}
        
        return scores
    
    def detect_with_smoothing(self, frame, face_region=None) -> EmotionResult:
        """
        Detect emotion with temporal smoothing
        Confirms emotion only when detected in multiple consecutive frames
        
        Args:
            frame: BGR image frame from camera
            face_region: Optional tuple (x, y, w, h) of face location
            
        Returns:
            EmotionResult with smoothed emotion detection
        """
        # Detect emotion in current frame
        result = self.detect_emotion(frame, face_region)
        
        # Add to buffer
        self.frame_buffer.append(result)
        
        # Keep only last N frames
        if len(self.frame_buffer) > self.smoothing_frames:
            self.frame_buffer.pop(0)
        
        # Check if we have enough frames for smoothing
        if len(self.frame_buffer) < self.smoothing_frames:
            return result
        
        # Check if same emotion detected in all frames
        emotions = [r.emotion for r in self.frame_buffer]
        if len(set(emotions)) == 1:
            # Same emotion in all frames - confirmed
            avg_confidence = sum(r.confidence for r in self.frame_buffer) / len(self.frame_buffer)
            
            return EmotionResult(
                emotion=emotions[0],
                confidence=avg_confidence,
                all_scores=result.all_scores,
                timestamp=datetime.now(),
                smoothed=True
            )
        else:
            # Mixed emotions - return most recent but mark as unsmoothed
            return result
