from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class EmotionRecord:
    """Record of detected emotion"""
    emotion: str
    confidence: float
    timestamp: datetime

@dataclass
class MoodChangeEvent:
    """Event representing a mood change"""
    previous_emotion: str
    current_emotion: str
    timestamp: datetime

class EmotionEngine:
    def __init__(self, config):
        self.config = config
        self.current_emotion = 'neutral'
        self.emotion_intensity = 0.5
        self.previous_emotion = 'neutral'
        
        # Emotion history tracking
        self.emotion_history: List[EmotionRecord] = []
        self.session_start = datetime.now()
    
    def record_emotion(self, emotion: str, confidence: float):
        """Record a detected emotion in history"""
        record = EmotionRecord(
            emotion=emotion,
            confidence=confidence,
            timestamp=datetime.now()
        )
        self.emotion_history.append(record)
    
    def get_emotion_history(self, time_window: float = 300) -> List[EmotionRecord]:
        """
        Get emotion history within time window
        
        Args:
            time_window: Time window in seconds (default 300 = 5 minutes)
            
        Returns:
            List of EmotionRecords within the time window
        """
        now = datetime.now()
        cutoff = now.timestamp() - time_window
        
        return [
            record for record in self.emotion_history
            if record.timestamp.timestamp() >= cutoff
        ]
    
    def check_mood_change(self, current_emotion: str) -> Optional[MoodChangeEvent]:
        """
        Check if mood has changed from previous state
        
        Args:
            current_emotion: Current detected emotion
            
        Returns:
            MoodChangeEvent if mood changed, None otherwise
        """
        if current_emotion != self.previous_emotion:
            event = MoodChangeEvent(
                previous_emotion=self.previous_emotion,
                current_emotion=current_emotion,
                timestamp=datetime.now()
            )
            self.previous_emotion = current_emotion
            return event
        return None
    
    def get_dominant_emotion(self, time_window: float = 300) -> str:
        """
        Calculate most frequent emotion in time window
        
        Args:
            time_window: Time window in seconds (default 300 = 5 minutes)
            
        Returns:
            Most frequent emotion string
        """
        history = self.get_emotion_history(time_window)
        
        if not history:
            return 'neutral'
        
        # Count emotion occurrences
        emotion_counts: Dict[str, int] = {}
        for record in history:
            emotion_counts[record.emotion] = emotion_counts.get(record.emotion, 0) + 1
        
        # Return most frequent
        return max(emotion_counts, key=emotion_counts.get)
    
    def get_session_statistics(self) -> Dict[str, any]:
        """
        Get emotion statistics for current session
        
        Returns:
            Dictionary with emotion distribution and statistics
        """
        if not self.emotion_history:
            return {
                'total_records': 0,
                'distribution': {},
                'session_duration': 0
            }
        
        # Calculate distribution
        emotion_counts: Dict[str, int] = {}
        for record in self.emotion_history:
            emotion_counts[record.emotion] = emotion_counts.get(record.emotion, 0) + 1
        
        total = len(self.emotion_history)
        distribution = {
            emotion: count / total
            for emotion, count in emotion_counts.items()
        }
        
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            'total_records': total,
            'distribution': distribution,
            'session_duration': session_duration,
            'dominant_emotion': self.get_dominant_emotion(session_duration)
        }
    
    def update(self, context):
        """Update AI's emotional state based on context"""
        user_mood = context.get('mood', 'unknown')
        hour = context.get('hour', 12)
        state_changes = context.get('state_changes', [])
        
        # Record detected emotion if available
        if user_mood != 'unknown':
            confidence = context.get('mood_confidence', 0.5)
            self.record_emotion(user_mood, confidence)
        
        # Determine emotion based on context
        if 'user_entered' in state_changes:
            self.current_emotion = 'happy'
            self.emotion_intensity = 0.7
        elif user_mood == 'sad':
            self.current_emotion = 'concerned'
            self.emotion_intensity = 0.8
        elif user_mood == 'tired' or (hour >= 23 or hour <= 5):
            self.current_emotion = 'supportive'
            self.emotion_intensity = 0.6
        elif context.get('user_speech'):
            self.current_emotion = 'curious'
            self.emotion_intensity = 0.7
        else:
            # Decay to neutral
            self.emotion_intensity *= 0.95
            if self.emotion_intensity < 0.3:
                self.current_emotion = 'neutral'
        
        return {
            'emotion': self.current_emotion,
            'intensity': self.emotion_intensity
        }
