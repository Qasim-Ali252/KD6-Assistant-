import cv2
import time
from datetime import datetime
from emotion.detector import EmotionDetector, DetectionError

class CameraPerception:
    def __init__(self, config):
        self.config = config
        self.camera_index = config['perception']['camera_index']
        
        # Try DirectShow backend first (more reliable on Windows)
        print(f"Opening camera {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        # Check if camera opened successfully
        if not self.cap.isOpened():
            print(f"⚠️  DirectShow failed, trying default backend...")
            self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            print(f"⚠️  Warning: Could not open camera at index {self.camera_index}")
            print("   Run 'python test_camera.py' to diagnose camera issues")
            print("   System will continue without camera (emotion detection disabled)")
        else:
            # Test read
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print(f"⚠️  Warning: Camera opened but cannot read frames")
                print("   Run 'python test_camera.py' to diagnose camera issues")
                print("   System will continue without camera (emotion detection disabled)")
            else:
                print(f"✓ Camera {self.camera_index} working: {frame.shape[1]}x{frame.shape[0]}")
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.last_detection_time = None
        self.user_present = False
        
        # Initialize emotion detector
        try:
            self.emotion_detector = EmotionDetector(config)
            print("✓ Emotion detector initialized")
        except Exception as e:
            print(f"Warning: Could not initialize emotion detector: {e}")
            self.emotion_detector = None
        
    def get_perception(self, skip_detection=False):
        """Detect presence and estimate mood using emotion detection
        
        Args:
            skip_detection: If True, return cached state without processing frame
        """
        # Fast path: return cached state without processing
        if skip_detection:
            return {
                'present': self.user_present,
                'mood': 'unknown',
                'mood_confidence': 0.0
            }
        
        ret, frame = self.cap.read()
        if not ret or frame is None:
            # Camera error - return not present
            return {'present': False, 'mood': 'unknown', 'mood_confidence': 0.0}
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        except Exception as e:
            # Error processing frame
            return {'present': False, 'mood': 'unknown', 'mood_confidence': 0.0}
        
        if len(faces) > 0:
            self.last_detection_time = time.time()
            self.user_present = True
            
            # Detect emotion if detector available
            mood = 'neutral'
            confidence = 0.5
            
            if self.emotion_detector is not None:
                try:
                    # Use first detected face
                    face_region = faces[0]
                    emotion_result = self.emotion_detector.detect_with_smoothing(frame, face_region)
                    mood = emotion_result.emotion
                    confidence = emotion_result.confidence
                except Exception as e:
                    # Fall back to neutral on error
                    pass
            
            return {
                'present': True,
                'mood': mood,
                'mood_confidence': confidence,
                'face_count': len(faces)
            }
        else:
            # Check timeout
            if self.last_detection_time:
                timeout = self.config['perception']['presence_timeout']
                if time.time() - self.last_detection_time > timeout:
                    self.user_present = False
            
            return {
                'present': self.user_present,
                'mood': 'unknown',
                'mood_confidence': 0.0
            }
    
    def release(self):
        self.cap.release()
