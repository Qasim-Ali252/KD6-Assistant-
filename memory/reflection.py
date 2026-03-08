"""
Self-Reflection Module
Analyzes interaction effectiveness and generates adaptation strategies
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

@dataclass
class ConversationTracking:
    """Tracks a conversation for effectiveness analysis"""
    conversation_id: str
    trigger_type: str
    topic: str
    start_time: datetime
    ai_message: str
    user_response: Optional[str] = None
    response_time: Optional[float] = None
    engagement: Optional[str] = None

@dataclass
class EffectivenessReport:
    """Report on conversation effectiveness"""
    time_window_days: int
    total_conversations: int
    engagement_distribution: Dict[str, float]
    trigger_effectiveness: Dict[str, float]
    topic_effectiveness: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AdaptationStrategy:
    """Strategy to adapt conversation behavior"""
    strategy_type: str  # 'reduce_frequency', 'increase_frequency', 'change_timing', 'change_topic'
    target: str  # What to adapt (trigger type, topic, etc.)
    modification: str  # Description of modification
    confidence: float
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True

@dataclass
class ReflectionReport:
    """Comprehensive reflection report"""
    timestamp: datetime
    effectiveness: EffectivenessReport
    patterns: List[str]
    strategies: List[AdaptationStrategy]
    recommendations: List[str]

class ReflectionModule:
    """Analyzes interaction effectiveness and generates adaptations"""
    
    def __init__(self, config):
        self.config = config
        reflection_config = config.get('reflection', {})
        
        self.idle_reflection_minutes = reflection_config.get('idle_reflection_minutes', 30)
        self.deep_reflection_hour = reflection_config.get('deep_reflection_hour', 3)
        self.effectiveness_window_days = reflection_config.get('effectiveness_window_days', 7)
        
        # Conversation tracking
        self.tracked_conversations: List[ConversationTracking] = []
        self.current_conversation: Optional[ConversationTracking] = None
        
        # Adaptation strategies
        self.strategies: List[AdaptationStrategy] = []
        
        # Timing
        self.last_idle_reflection: Optional[datetime] = None
        self.last_deep_reflection: Optional[datetime] = None
        self.last_activity_time: float = time.time()
    
    def track_conversation(self, conversation_id: str, trigger_type: str, 
                          topic: str, ai_message: str):
        """
        Begin tracking a conversation
        
        Args:
            conversation_id: Unique identifier for conversation
            trigger_type: Type of trigger that initiated conversation
            topic: Conversation topic
            ai_message: AI's message
        """
        self.current_conversation = ConversationTracking(
            conversation_id=conversation_id,
            trigger_type=trigger_type,
            topic=topic,
            start_time=datetime.now(),
            ai_message=ai_message
        )
        
        self.last_activity_time = time.time()
    
    def record_user_response(self, user_response: str, response_time: float):
        """
        Record user's response to tracked conversation
        
        Args:
            user_response: User's response text
            response_time: Time taken to respond in seconds
        """
        if self.current_conversation is None:
            return
        
        self.current_conversation.user_response = user_response
        self.current_conversation.response_time = response_time
        
        # Classify engagement
        self.current_conversation.engagement = self.classify_engagement(
            user_response, response_time
        )
        
        # Store completed conversation
        self.tracked_conversations.append(self.current_conversation)
        self.current_conversation = None
        
        self.last_activity_time = time.time()
    
    def classify_engagement(self, user_response: Optional[str], 
                           response_time: float) -> str:
        """
        Classify user engagement level
        
        Args:
            user_response: User's response (None if no response)
            response_time: Time taken to respond in seconds
            
        Returns:
            'engaged', 'neutral', or 'dismissive'
        """
        if user_response is None:
            return 'dismissive'
        
        # Quick response (< 30s) indicates engagement
        if response_time < 30:
            return 'engaged'
        
        # Very slow response (> 120s) indicates dismissive
        if response_time > 120:
            return 'dismissive'
        
        # Check response length
        if len(user_response) > 20:
            return 'engaged'
        elif len(user_response) < 5:
            return 'dismissive'
        
        return 'neutral'
    
    def analyze_effectiveness(self, time_window_days: int = 7) -> EffectivenessReport:
        """
        Analyze conversation effectiveness over time window
        
        Args:
            time_window_days: Number of days to analyze
            
        Returns:
            EffectivenessReport with statistics
        """
        cutoff = datetime.now() - timedelta(days=time_window_days)
        
        # Filter conversations in window
        recent = [
            conv for conv in self.tracked_conversations
            if conv.start_time >= cutoff and conv.engagement is not None
        ]
        
        if not recent:
            return EffectivenessReport(
                time_window_days=time_window_days,
                total_conversations=0,
                engagement_distribution={},
                trigger_effectiveness={},
                topic_effectiveness={}
            )
        
        # Calculate engagement distribution
        engagement_counts = {}
        for conv in recent:
            engagement_counts[conv.engagement] = engagement_counts.get(conv.engagement, 0) + 1
        
        total = len(recent)
        engagement_distribution = {
            eng: count / total
            for eng, count in engagement_counts.items()
        }
        
        # Calculate trigger effectiveness
        trigger_stats: Dict[str, Dict[str, int]] = {}
        for conv in recent:
            if conv.trigger_type not in trigger_stats:
                trigger_stats[conv.trigger_type] = {'total': 0, 'engaged': 0}
            trigger_stats[conv.trigger_type]['total'] += 1
            if conv.engagement == 'engaged':
                trigger_stats[conv.trigger_type]['engaged'] += 1
        
        trigger_effectiveness = {
            trigger: stats['engaged'] / stats['total']
            for trigger, stats in trigger_stats.items()
        }
        
        # Calculate topic effectiveness
        topic_stats: Dict[str, Dict[str, int]] = {}
        for conv in recent:
            if conv.topic not in topic_stats:
                topic_stats[conv.topic] = {'total': 0, 'engaged': 0}
            topic_stats[conv.topic]['total'] += 1
            if conv.engagement == 'engaged':
                topic_stats[conv.topic]['engaged'] += 1
        
        topic_effectiveness = {
            topic: stats['engaged'] / stats['total']
            for topic, stats in topic_stats.items()
        }
        
        return EffectivenessReport(
            time_window_days=time_window_days,
            total_conversations=total,
            engagement_distribution=engagement_distribution,
            trigger_effectiveness=trigger_effectiveness,
            topic_effectiveness=topic_effectiveness
        )
    
    def check_idle_reflection(self) -> bool:
        """
        Check if idle reflection should be triggered
        
        Returns:
            True if reflection should be performed
        """
        idle_time = time.time() - self.last_activity_time
        idle_threshold = self.idle_reflection_minutes * 60
        
        if idle_time >= idle_threshold:
            # Check if we already did reflection recently
            if self.last_idle_reflection is None:
                return True
            
            time_since_last = (datetime.now() - self.last_idle_reflection).total_seconds()
            if time_since_last >= idle_threshold:
                return True
        
        return False
    
    def perform_idle_reflection(self) -> ReflectionReport:
        """
        Perform reflection during idle period
        
        Returns:
            ReflectionReport with analysis
        """
        self.last_idle_reflection = datetime.now()
        
        # Analyze recent effectiveness
        effectiveness = self.analyze_effectiveness(time_window_days=7)
        
        # Identify patterns
        patterns = self._identify_effectiveness_patterns(effectiveness)
        
        # Generate adaptation strategies
        new_strategies = self.generate_adaptations(effectiveness)
        
        # Add new strategies
        self.strategies.extend(new_strategies)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(effectiveness, patterns)
        
        return ReflectionReport(
            timestamp=datetime.now(),
            effectiveness=effectiveness,
            patterns=patterns,
            strategies=new_strategies,
            recommendations=recommendations
        )
    
    def _identify_effectiveness_patterns(self, effectiveness: EffectivenessReport) -> List[str]:
        """Identify patterns from effectiveness data"""
        patterns = []
        
        # Low effectiveness triggers
        for trigger, score in effectiveness.trigger_effectiveness.items():
            if score < 0.3:
                patterns.append(f"Low effectiveness for {trigger} trigger ({score:.1%})")
        
        # High effectiveness triggers
        for trigger, score in effectiveness.trigger_effectiveness.items():
            if score > 0.7:
                patterns.append(f"High effectiveness for {trigger} trigger ({score:.1%})")
        
        # Low effectiveness topics
        for topic, score in effectiveness.topic_effectiveness.items():
            if score < 0.3:
                patterns.append(f"Low engagement with {topic} topic ({score:.1%})")
        
        # High effectiveness topics
        for topic, score in effectiveness.topic_effectiveness.items():
            if score > 0.7:
                patterns.append(f"High engagement with {topic} topic ({score:.1%})")
        
        return patterns
    
    def generate_adaptations(self, effectiveness: EffectivenessReport) -> List[AdaptationStrategy]:
        """
        Generate adaptation strategies from effectiveness data
        
        Args:
            effectiveness: EffectivenessReport to analyze
            
        Returns:
            List of AdaptationStrategy objects
        """
        strategies = []
        
        # Reduce frequency of low-effectiveness triggers
        for trigger, score in effectiveness.trigger_effectiveness.items():
            if score < 0.3:
                strategies.append(AdaptationStrategy(
                    strategy_type='reduce_frequency',
                    target=trigger,
                    modification=f'Reduce {trigger} frequency by 50%',
                    confidence=1 - score
                ))
        
        # Increase frequency of high-effectiveness triggers
        for trigger, score in effectiveness.trigger_effectiveness.items():
            if score > 0.7:
                strategies.append(AdaptationStrategy(
                    strategy_type='increase_frequency',
                    target=trigger,
                    modification=f'Increase {trigger} frequency by 30%',
                    confidence=score
                ))
        
        # Avoid low-effectiveness topics
        for topic, score in effectiveness.topic_effectiveness.items():
            if score < 0.3:
                strategies.append(AdaptationStrategy(
                    strategy_type='change_topic',
                    target=topic,
                    modification=f'Avoid {topic} topic',
                    confidence=1 - score
                ))
        
        return strategies
    
    def _generate_recommendations(self, effectiveness: EffectivenessReport, 
                                  patterns: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if effectiveness.total_conversations == 0:
            recommendations.append("Insufficient data for recommendations")
            return recommendations
        
        # Overall engagement
        engaged_rate = effectiveness.engagement_distribution.get('engaged', 0)
        if engaged_rate < 0.3:
            recommendations.append("Overall engagement is low - consider adjusting conversation style")
        elif engaged_rate > 0.6:
            recommendations.append("Overall engagement is good - maintain current approach")
        
        # Specific improvements
        if len(effectiveness.trigger_effectiveness) > 0:
            worst_trigger = min(effectiveness.trigger_effectiveness, 
                              key=effectiveness.trigger_effectiveness.get)
            recommendations.append(f"Consider reducing or modifying {worst_trigger} trigger")
        
        return recommendations
    
    def perform_deep_reflection(self) -> ReflectionReport:
        """
        Perform deep reflection on last 100 interactions
        
        Returns:
            Comprehensive ReflectionReport
        """
        self.last_deep_reflection = datetime.now()
        
        # Analyze longer time window
        effectiveness = self.analyze_effectiveness(time_window_days=30)
        
        # Identify patterns
        patterns = self._identify_effectiveness_patterns(effectiveness)
        
        # Generate comprehensive strategies
        strategies = self.generate_adaptations(effectiveness)
        
        # Generate detailed recommendations
        recommendations = self._generate_recommendations(effectiveness, patterns)
        
        return ReflectionReport(
            timestamp=datetime.now(),
            effectiveness=effectiveness,
            patterns=patterns,
            strategies=strategies,
            recommendations=recommendations
        )
    
    def evaluate_strategy(self, strategy: AdaptationStrategy) -> Dict:
        """
        Evaluate effectiveness of an active strategy
        
        Args:
            strategy: Strategy to evaluate
            
        Returns:
            Dictionary with evaluation results
        """
        if not strategy.active:
            return {'evaluated': False, 'reason': 'Strategy not active'}
        
        # Check if strategy has been active for at least 7 days
        days_active = (datetime.now() - strategy.created_at).days
        if days_active < 7:
            return {'evaluated': False, 'reason': 'Insufficient time'}
        
        # Get effectiveness before and after strategy
        # This is simplified - in production, you'd track baseline metrics
        current_effectiveness = self.analyze_effectiveness(time_window_days=7)
        
        # Check if overall engagement improved
        engaged_rate = current_effectiveness.engagement_distribution.get('engaged', 0)
        
        # If engagement is very low, deactivate strategy
        if engaged_rate < 0.2:
            strategy.active = False
            return {
                'evaluated': True,
                'result': 'negative',
                'action': 'deactivated',
                'engagement_rate': engaged_rate
            }
        
        return {
            'evaluated': True,
            'result': 'positive' if engaged_rate > 0.4 else 'neutral',
            'engagement_rate': engaged_rate
        }
    
    def get_active_strategies(self) -> List[AdaptationStrategy]:
        """Get list of currently active strategies"""
        return [s for s in self.strategies if s.active]
