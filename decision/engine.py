import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List

@dataclass
class TriggerDecision:
    """Decision to trigger a proactive conversation"""
    trigger_type: str
    priority: int
    context: Dict
    reason: str

class DecisionEngine:
    def __init__(self, config):
        self.config = config
        self.last_interaction_time = time.time()
        self.idle_threshold = config['decision']['idle_threshold']
        
        # Trigger tracking for rate limiting
        self.trigger_history: Dict[str, List[float]] = {}
        
        # Activity tracking
        self.focus_start_time: Optional[float] = None
        self.last_activity: str = 'unknown'
        self.in_meeting: bool = False
    
    def evaluate(self, context, emotion, memory):
        """Decide if AI should respond and why"""
        
        # User spoke - always respond
        if context.get('user_speech'):
            self.last_interaction_time = time.time()
            return {
                'should_respond': True,
                'reason': 'user_spoke',
                'user_input': context['user_speech']
            }
        
        # User just entered - greet (but not if we just interacted recently)
        if 'user_entered' in context.get('state_changes', []):
            # Don't greet if we interacted in the last 2 minutes (active conversation)
            time_since_interaction = time.time() - self.last_interaction_time
            if time_since_interaction > 120:  # 2 minutes
                if self.config['decision']['greeting_enabled']:
                    self.last_interaction_time = time.time()
                    return {
                        'should_respond': True,
                        'reason': 'user_entered'
                    }
        
        # Proactive behavior - user idle too long
        if self.config['decision']['proactive_enabled']:
            if context['user_present']:
                idle_time = time.time() - self.last_interaction_time
                if idle_time > self.idle_threshold:
                    self.last_interaction_time = time.time()
                    return {
                        'should_respond': True,
                        'reason': 'proactive_idle'
                    }
        
        # Late night concern
        if context['hour'] >= 2 and context['hour'] <= 4:
            if context['user_present']:
                # Check if we already mentioned this recently
                recent = memory.get_recent(limit=3)
                if not any('late_night' in str(r) for r in recent):
                    self.last_interaction_time = time.time()
                    return {
                        'should_respond': True,
                        'reason': 'late_night_concern'
                    }
        
        return {'should_respond': False}

    
    def infer_activity(self, emotion_history: List) -> str:
        """
        Infer user activity from emotion patterns
        
        Args:
            emotion_history: List of recent emotion records
            
        Returns:
            Inferred activity string
        """
        if not emotion_history:
            return 'unknown'
        
        # Check for extended focus period
        recent_emotions = [r.emotion for r in emotion_history[-10:]]
        focus_count = recent_emotions.count('focused') + recent_emotions.count('neutral')
        
        if focus_count >= 7:
            # Extended focus detected
            if self.focus_start_time is None:
                self.focus_start_time = time.time()
            return 'working'
        else:
            # Check for transition from focus
            if self.focus_start_time is not None:
                # Was focused, now not - likely break or completion
                self.focus_start_time = None
                
                # Check if tired or neutral - suggests break
                if recent_emotions[-1] in ['tired', 'neutral']:
                    return 'break'
                elif recent_emotions[-1] in ['happy', 'satisfied']:
                    return 'completion'
            
            self.focus_start_time = None
            return 'idle'
    
    def record_trigger_fired(self, trigger_type: str):
        """Record that a trigger was fired for rate limiting"""
        now = time.time()
        if trigger_type not in self.trigger_history:
            self.trigger_history[trigger_type] = []
        
        self.trigger_history[trigger_type].append(now)
        
        # Clean old entries (older than 1 hour)
        cutoff = now - 3600
        self.trigger_history[trigger_type] = [
            t for t in self.trigger_history[trigger_type] if t >= cutoff
        ]
    
    def should_suppress(self) -> bool:
        """Check if proactive triggers should be suppressed"""
        # Suppress if in meeting
        if self.in_meeting:
            return True
        
        return False
    
    def can_trigger(self, trigger_type: str, min_interval: int = 600) -> bool:
        """
        Check if trigger can fire based on rate limiting
        
        Args:
            trigger_type: Type of trigger to check
            min_interval: Minimum interval in seconds (default 600 = 10 minutes)
            
        Returns:
            True if trigger can fire, False otherwise
        """
        if trigger_type not in self.trigger_history:
            return True
        
        now = time.time()
        last_trigger = max(self.trigger_history[trigger_type]) if self.trigger_history[trigger_type] else 0
        
        return (now - last_trigger) >= min_interval
    
    def evaluate_triggers(self, context: Dict, emotion_history: List) -> Optional[TriggerDecision]:
        """
        Evaluate all proactive conversation triggers
        
        Args:
            context: Current context dictionary
            emotion_history: Recent emotion history
            
        Returns:
            TriggerDecision if a trigger should fire, None otherwise
        """
        # Check suppression
        if self.should_suppress():
            return None
        
        current_emotion = context.get('mood', 'neutral')
        hour = context.get('hour', 12)
        user_present = context.get('user_present', False)
        
        if not user_present:
            return None
        
        # Don't interrupt if user just spoke (active conversation)
        if context.get('user_speech'):
            return None
        
        # Check if there was recent interaction (within last 2 minutes)
        time_since_interaction = time.time() - self.last_interaction_time
        if time_since_interaction < 120:  # 2 minutes
            return None
        
        # Priority 1: Sad/Angry mood - supportive response (but not too frequently)
        if current_emotion in ['sad', 'angry']:
            # Longer interval for supportive mood - 10 minutes minimum
            if self.can_trigger('supportive_mood', min_interval=600):
                return TriggerDecision(
                    trigger_type='supportive_mood',
                    priority=1,
                    context={'emotion': current_emotion},
                    reason=f'User appears {current_emotion}, offering support'
                )
        
        # Priority 2: Late night tired - rest suggestion (22:00-06:00)
        if current_emotion == 'tired' and (hour >= 22 or hour <= 6):
            if self.can_trigger('rest_suggestion', min_interval=1800):  # 30 min
                return TriggerDecision(
                    trigger_type='rest_suggestion',
                    priority=2,
                    context={'hour': hour, 'emotion': current_emotion},
                    reason='User appears tired late at night'
                )
        
        # Priority 3: Extended focus - break suggestion (>60 min)
        if self.focus_start_time is not None:
            focus_duration = time.time() - self.focus_start_time
            if focus_duration > 3600:  # 60 minutes
                if self.can_trigger('break_suggestion', min_interval=1800):  # 30 min
                    return TriggerDecision(
                        trigger_type='break_suggestion',
                        priority=3,
                        context={'focus_duration': focus_duration / 60},
                        reason=f'User has been focused for {focus_duration/60:.0f} minutes'
                    )
        
        # Priority 4: Happy completion - reinforcement
        activity = self.infer_activity(emotion_history)
        if activity == 'completion' and current_emotion == 'happy':
            if self.can_trigger('completion_reinforcement', min_interval=600):
                return TriggerDecision(
                    trigger_type='completion_reinforcement',
                    priority=4,
                    context={'emotion': current_emotion},
                    reason='User appears to have completed something'
                )
        
        # Priority 5: Return greeting (>4 hours absence)
        idle_time = time.time() - self.last_interaction_time
        if idle_time > 14400:  # 4 hours
            if self.can_trigger('return_greeting', min_interval=14400):
                return TriggerDecision(
                    trigger_type='return_greeting',
                    priority=5,
                    context={'absence_hours': idle_time / 3600},
                    reason=f'User returned after {idle_time/3600:.1f} hours'
                )
        
        return None
