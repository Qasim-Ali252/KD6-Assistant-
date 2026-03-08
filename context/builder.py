from datetime import datetime

class ContextBuilder:
    def __init__(self, config):
        self.config = config
        self.previous_context = None
    
    def build(self, perception_data, memory):
        """Build current context from perception and memory"""
        now = datetime.now()
        
        context = {
            'timestamp': now.isoformat(),
            'time': now.strftime('%I:%M %p'),
            'hour': now.hour,
            'user_present': perception_data['camera']['present'],
            'mood': perception_data['camera'].get('mood', 'unknown'),
            'user_speech': perception_data['audio'],
            'recent_memory': memory.get_recent(limit=5),
            'user_preferences': memory.get_preferences()
        }
        
        # Detect state changes
        if self.previous_context:
            context['state_changes'] = self._detect_changes(context)
        else:
            context['state_changes'] = []
        
        self.previous_context = context
        return context
    
    def _detect_changes(self, current):
        """Detect important state changes"""
        changes = []
        prev = self.previous_context
        
        if not prev['user_present'] and current['user_present']:
            changes.append('user_entered')
        elif prev['user_present'] and not current['user_present']:
            changes.append('user_left')
        
        if prev['mood'] != current['mood'] and current['mood'] != 'unknown':
            changes.append(f"mood_changed_to_{current['mood']}")
        
        return changes
