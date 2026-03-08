"""
Preference Learning Module
Learns user preferences from interaction patterns
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import json

@dataclass
class InteractionRecord:
    """Record of a user interaction"""
    timestamp: datetime
    trigger_type: str
    conversation_topic: str
    user_response: Optional[str]
    engagement: str  # 'positive', 'neutral', 'ignored'
    response_time: float  # seconds

@dataclass
class InteractionPattern:
    """Identified pattern in user interactions"""
    pattern_type: str  # 'time_based', 'topic', 'style'
    description: str
    frequency: int
    confidence: float
    metadata: Dict = field(default_factory=dict)

@dataclass
class TimeWindow:
    """Time window with engagement score"""
    start_hour: int
    end_hour: int
    engagement_score: float

@dataclass
class PreferenceProfile:
    """User preference profile"""
    topic_preferences: Dict[str, float] = field(default_factory=dict)
    conversation_style: str = 'balanced'  # 'brief', 'balanced', 'detailed'
    formality_level: str = 'casual'  # 'casual', 'formal'
    preferred_times: List[TimeWindow] = field(default_factory=list)
    suppressed_suggestions: List[str] = field(default_factory=list)

class PreferenceLearner:
    """Learns user preferences from interactions"""
    
    def __init__(self, config):
        self.config = config
        learning_config = config.get('learning', {})
        
        self.min_interactions = learning_config.get('min_interactions_for_patterns', 10)
        self.confidence_threshold = learning_config.get('preference_confidence_threshold', 0.6)
        
        # Interaction history
        self.interactions: List[InteractionRecord] = []
        
        # Identified patterns
        self.patterns: List[InteractionPattern] = []
        
        # Suggestion priority tracking
        self.suggestion_ignores: Dict[str, List[datetime]] = {}
        self.low_priority_suggestions: List[str] = []
        self.suppressed_suggestions: List[str] = []
    
    def record_interaction(self, trigger_type: str, topic: str, user_response: Optional[str],
                          engagement: str, response_time: float):
        """
        Record a user interaction
        
        Args:
            trigger_type: Type of trigger that initiated conversation
            topic: Conversation topic
            user_response: User's response text (None if ignored)
            engagement: 'positive', 'neutral', or 'ignored'
            response_time: Time taken to respond in seconds
        """
        record = InteractionRecord(
            timestamp=datetime.now(),
            trigger_type=trigger_type,
            conversation_topic=topic,
            user_response=user_response,
            engagement=engagement,
            response_time=response_time
        )
        
        self.interactions.append(record)
        
        # Track ignores for suggestion priority
        if engagement == 'ignored':
            suggestion_key = f"{trigger_type}:{topic}"
            if suggestion_key not in self.suggestion_ignores:
                self.suggestion_ignores[suggestion_key] = []
            self.suggestion_ignores[suggestion_key].append(datetime.now())
            
            # Update suggestion priority
            self.update_suggestion_priority(suggestion_key)
    
    def analyze_patterns(self) -> List[InteractionPattern]:
        """
        Analyze interaction history to identify patterns
        
        Returns:
            List of identified patterns
        """
        if len(self.interactions) < self.min_interactions:
            return []
        
        patterns = []
        
        # Time-based patterns
        time_patterns = self._analyze_time_patterns()
        patterns.extend(time_patterns)
        
        # Topic preferences
        topic_patterns = self._analyze_topic_patterns()
        patterns.extend(topic_patterns)
        
        # Style preferences
        style_patterns = self._analyze_style_patterns()
        patterns.extend(style_patterns)
        
        # Store patterns
        self.patterns = patterns
        
        return patterns
    
    def _analyze_time_patterns(self) -> List[InteractionPattern]:
        """Analyze time-based interaction patterns"""
        patterns = []
        
        # Group interactions by hour
        hour_engagement: Dict[int, List[str]] = {}
        for interaction in self.interactions:
            hour = interaction.timestamp.hour
            if hour not in hour_engagement:
                hour_engagement[hour] = []
            hour_engagement[hour].append(interaction.engagement)
        
        # Find hours with high engagement
        for hour, engagements in hour_engagement.items():
            if len(engagements) >= 3:  # Minimum 3 occurrences
                positive_rate = engagements.count('positive') / len(engagements)
                if positive_rate >= 0.6:
                    patterns.append(InteractionPattern(
                        pattern_type='time_based',
                        description=f'High engagement around {hour}:00',
                        frequency=len(engagements),
                        confidence=positive_rate,
                        metadata={'hour': hour}
                    ))
        
        return patterns
    
    def _analyze_topic_patterns(self) -> List[InteractionPattern]:
        """Analyze topic preference patterns"""
        patterns = []
        
        # Group by topic
        topic_engagement: Dict[str, List[str]] = {}
        for interaction in self.interactions:
            topic = interaction.conversation_topic
            if topic not in topic_engagement:
                topic_engagement[topic] = []
            topic_engagement[topic].append(interaction.engagement)
        
        # Find preferred topics
        for topic, engagements in topic_engagement.items():
            if len(engagements) >= 3:
                positive_rate = engagements.count('positive') / len(engagements)
                if positive_rate >= 0.6:
                    patterns.append(InteractionPattern(
                        pattern_type='topic',
                        description=f'Prefers topic: {topic}',
                        frequency=len(engagements),
                        confidence=positive_rate,
                        metadata={'topic': topic, 'preference': 'high'}
                    ))
                elif positive_rate <= 0.3:
                    patterns.append(InteractionPattern(
                        pattern_type='topic',
                        description=f'Dislikes topic: {topic}',
                        frequency=len(engagements),
                        confidence=1 - positive_rate,
                        metadata={'topic': topic, 'preference': 'low'}
                    ))
        
        return patterns
    
    def _analyze_style_patterns(self) -> List[InteractionPattern]:
        """Analyze conversation style preferences"""
        patterns = []
        
        # Analyze response lengths
        response_lengths = [
            len(i.user_response) for i in self.interactions
            if i.user_response is not None
        ]
        
        if len(response_lengths) >= 5:
            avg_length = sum(response_lengths) / len(response_lengths)
            
            if avg_length < 50:
                patterns.append(InteractionPattern(
                    pattern_type='style',
                    description='Prefers brief responses',
                    frequency=len(response_lengths),
                    confidence=0.7,
                    metadata={'style': 'brief', 'avg_length': avg_length}
                ))
            elif avg_length > 150:
                patterns.append(InteractionPattern(
                    pattern_type='style',
                    description='Prefers detailed responses',
                    frequency=len(response_lengths),
                    confidence=0.7,
                    metadata={'style': 'detailed', 'avg_length': avg_length}
                ))
        
        return patterns
    
    def get_preferences(self) -> PreferenceProfile:
        """
        Generate preference profile from patterns
        
        Returns:
            PreferenceProfile with current preferences
        """
        # Analyze patterns if not done recently
        if len(self.interactions) >= self.min_interactions:
            self.analyze_patterns()
        
        profile = PreferenceProfile()
        
        # Extract topic preferences
        for pattern in self.patterns:
            if pattern.pattern_type == 'topic':
                topic = pattern.metadata.get('topic')
                preference = pattern.metadata.get('preference')
                if topic and preference == 'high':
                    profile.topic_preferences[topic] = pattern.confidence
        
        # Extract style preferences
        for pattern in self.patterns:
            if pattern.pattern_type == 'style':
                style = pattern.metadata.get('style')
                if style:
                    profile.conversation_style = style
        
        # Extract preferred times
        for pattern in self.patterns:
            if pattern.pattern_type == 'time_based':
                hour = pattern.metadata.get('hour')
                if hour is not None:
                    profile.preferred_times.append(TimeWindow(
                        start_hour=hour,
                        end_hour=(hour + 1) % 24,
                        engagement_score=pattern.confidence
                    ))
        
        # Add suppressed suggestions
        profile.suppressed_suggestions = self.suppressed_suggestions.copy()
        
        return profile
    
    def update_suggestion_priority(self, suggestion_key: str):
        """
        Update priority of a suggestion based on ignore history
        
        Args:
            suggestion_key: Key identifying the suggestion
        """
        if suggestion_key not in self.suggestion_ignores:
            return
        
        ignores = self.suggestion_ignores[suggestion_key]
        
        # Check for 3 consecutive ignores
        if len(ignores) >= 3:
            if suggestion_key not in self.low_priority_suggestions:
                self.low_priority_suggestions.append(suggestion_key)
        
        # Check for 5 ignores in 7 days
        now = datetime.now()
        recent_ignores = [
            ig for ig in ignores
            if (now - ig).days <= 7
        ]
        
        if len(recent_ignores) >= 5:
            if suggestion_key not in self.suppressed_suggestions:
                self.suppressed_suggestions.append(suggestion_key)
    
    def restore_suggestion_priority(self, suggestion_key: str):
        """
        Restore priority of a suggestion after positive engagement
        
        Args:
            suggestion_key: Key identifying the suggestion
        """
        if suggestion_key in self.low_priority_suggestions:
            self.low_priority_suggestions.remove(suggestion_key)
        
        if suggestion_key in self.suppressed_suggestions:
            self.suppressed_suggestions.remove(suggestion_key)
        
        # Clear ignore history
        if suggestion_key in self.suggestion_ignores:
            self.suggestion_ignores[suggestion_key] = []
    
    def get_preferred_times(self) -> List[TimeWindow]:
        """
        Get preferred time windows for conversations
        
        Returns:
            List of TimeWindow objects with engagement scores
        """
        profile = self.get_preferences()
        return profile.preferred_times
    
    def is_low_priority(self, suggestion_key: str) -> bool:
        """Check if suggestion is low priority"""
        return suggestion_key in self.low_priority_suggestions
    
    def is_suppressed(self, suggestion_key: str) -> bool:
        """Check if suggestion is suppressed"""
        return suggestion_key in self.suppressed_suggestions
