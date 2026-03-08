import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class MemoryManager:
    def __init__(self, config):
        self.config = config
        self.memory_file = 'memory/storage.json'
        self.preferences_file = 'memory/preferences.json'
        self.patterns_file = 'memory/patterns.json'
        self.strategies_file = 'memory/strategies.json'
        self.reports_dir = 'memory/reflection_reports'
        
        self.short_term = []  # Recent conversation
        self.long_term = {}   # Persistent facts
        self.episodic = []    # Past events
        
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.long_term = data.get('long_term', {})
                    self.episodic = data.get('episodic', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load memory: {e}")
                self.long_term = {}
                self.episodic = []
    
    def _save_memory(self):
        """Save memory to disk with corruption prevention"""
        os.makedirs('memory', exist_ok=True)
        
        # Create backup before saving
        if os.path.exists(self.memory_file):
            backup_file = self.memory_file + '.backup'
            try:
                import shutil
                shutil.copy2(self.memory_file, backup_file)
            except:
                pass
        
        # Prepare data
        data = {
            'long_term': self.long_term,
            'episodic': self.episodic[-100:]  # Keep last 100 episodes
        }
        
        # Write to temporary file first
        temp_file = self.memory_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # If write successful, replace original
            import shutil
            shutil.move(temp_file, self.memory_file)
        except Exception as e:
            print(f"Error saving memory: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def add_interaction(self, context, response):
        """Store an interaction"""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'response': response
        }
        
        self.short_term.append(interaction)
        if len(self.short_term) > 20:
            self.short_term.pop(0)
        
        self.episodic.append(interaction)
        self._save_memory()
    
    def get_recent(self, limit=5):
        """Get recent interactions"""
        return self.short_term[-limit:]
    
    def get_preferences(self):
        """Get user preferences"""
        return self.long_term.get('preferences', {})
    
    def store_fact(self, key, value):
        """Store a long-term fact"""
        self.long_term[key] = value
        self._save_memory()

    
    def get_relevant_context(self, current_context: Dict, limit: int = 5) -> List[Dict]:
        """
        Get relevant past interactions based on current context
        
        Args:
            current_context: Current context dictionary
            limit: Maximum number of interactions to return
            
        Returns:
            List of relevant past interactions
        """
        if not self.episodic:
            return []
        
        current_emotion = current_context.get('mood', 'neutral')
        current_hour = current_context.get('hour', 12)
        
        # Score each past interaction for relevance
        scored_interactions = []
        for interaction in self.episodic[-50:]:  # Check last 50
            score = 0
            
            # Same emotion context
            if interaction.get('context', {}).get('mood') == current_emotion:
                score += 2
            
            # Similar time of day (within 2 hours)
            past_hour = interaction.get('context', {}).get('hour', 12)
            if abs(past_hour - current_hour) <= 2:
                score += 1
            
            # Recent interactions score higher
            scored_interactions.append((score, interaction))
        
        # Sort by score and return top N
        scored_interactions.sort(key=lambda x: x[0], reverse=True)
        return [interaction for score, interaction in scored_interactions[:limit]]
    
    def store_preference_data(self, preference_profile):
        """
        Persist preference profile to disk
        
        Args:
            preference_profile: PreferenceProfile object to store
        """
        os.makedirs('memory', exist_ok=True)
        
        # Convert to dict
        data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'topic_preferences': preference_profile.topic_preferences,
            'conversation_style': preference_profile.conversation_style,
            'formality_level': preference_profile.formality_level,
            'preferred_times': [
                {
                    'start_hour': tw.start_hour,
                    'end_hour': tw.end_hour,
                    'engagement_score': tw.engagement_score
                }
                for tw in preference_profile.preferred_times
            ],
            'suppressed_suggestions': preference_profile.suppressed_suggestions
        }
        
        # Create backup
        if os.path.exists(self.preferences_file):
            backup_file = self.preferences_file + '.backup'
            try:
                os.replace(self.preferences_file, backup_file)
            except:
                pass
        
        # Write new data
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving preferences: {e}")
    
    def load_preference_data(self):
        """
        Load preference profile from disk
        
        Returns:
            Dictionary with preference data or None
        """
        if not os.path.exists(self.preferences_file):
            return None
        
        try:
            with open(self.preferences_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading preferences: {e}")
            return None
    
    def store_patterns(self, patterns: List):
        """
        Persist interaction patterns to disk
        
        Args:
            patterns: List of InteractionPattern objects
        """
        os.makedirs('memory', exist_ok=True)
        
        data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'patterns': [
                {
                    'pattern_type': p.pattern_type,
                    'description': p.description,
                    'frequency': p.frequency,
                    'confidence': p.confidence,
                    'metadata': p.metadata
                }
                for p in patterns
            ]
        }
        
        # Create backup
        if os.path.exists(self.patterns_file):
            backup_file = self.patterns_file + '.backup'
            try:
                os.replace(self.patterns_file, backup_file)
            except:
                pass
        
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving patterns: {e}")
    
    def load_patterns(self):
        """Load interaction patterns from disk"""
        if not os.path.exists(self.patterns_file):
            return None
        
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading patterns: {e}")
            return None
    
    def store_strategies(self, strategies: List):
        """
        Persist adaptation strategies to disk
        
        Args:
            strategies: List of AdaptationStrategy objects
        """
        os.makedirs('memory', exist_ok=True)
        
        data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'strategies': [
                {
                    'strategy_type': s.strategy_type,
                    'target': s.target,
                    'modification': s.modification,
                    'confidence': s.confidence,
                    'created_at': s.created_at.isoformat(),
                    'active': s.active
                }
                for s in strategies
            ]
        }
        
        # Create backup
        if os.path.exists(self.strategies_file):
            backup_file = self.strategies_file + '.backup'
            try:
                os.replace(self.strategies_file, backup_file)
            except:
                pass
        
        try:
            with open(self.strategies_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving strategies: {e}")
    
    def load_strategies(self):
        """Load adaptation strategies from disk"""
        if not os.path.exists(self.strategies_file):
            return None
        
        try:
            with open(self.strategies_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading strategies: {e}")
            return None
    
    def store_reflection_report(self, report):
        """
        Store reflection report to disk
        
        Args:
            report: ReflectionReport object
        """
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Create filename with timestamp
        filename = f"reflection_{report.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        data = {
            'timestamp': report.timestamp.isoformat(),
            'effectiveness': {
                'time_window_days': report.effectiveness.time_window_days,
                'total_conversations': report.effectiveness.total_conversations,
                'engagement_distribution': report.effectiveness.engagement_distribution,
                'trigger_effectiveness': report.effectiveness.trigger_effectiveness,
                'topic_effectiveness': report.effectiveness.topic_effectiveness
            },
            'patterns': report.patterns,
            'strategies': [
                {
                    'strategy_type': s.strategy_type,
                    'target': s.target,
                    'modification': s.modification,
                    'confidence': s.confidence
                }
                for s in report.strategies
            ],
            'recommendations': report.recommendations
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving reflection report: {e}")
    
    def get_recent_reflection_report(self):
        """Get most recent reflection report"""
        if not os.path.exists(self.reports_dir):
            return None
        
        # Find most recent report file
        files = [f for f in os.listdir(self.reports_dir) if f.startswith('reflection_')]
        if not files:
            return None
        
        files.sort(reverse=True)
        latest_file = os.path.join(self.reports_dir, files[0])
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading reflection report: {e}")
            return None
    
    def export_learning_data(self, export_path: str):
        """
        Export all learning data to a backup file
        
        Args:
            export_path: Path to export file
        """
        data = {
            'version': '1.0',
            'export_timestamp': datetime.now().isoformat(),
            'preferences': self.load_preference_data(),
            'patterns': self.load_patterns(),
            'strategies': self.load_strategies()
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Learning data exported to {export_path}")
        except IOError as e:
            print(f"Error exporting learning data: {e}")
    
    def import_learning_data(self, import_path: str):
        """
        Import learning data from a backup file
        
        Args:
            import_path: Path to import file
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore each component
            if data.get('preferences'):
                with open(self.preferences_file, 'w', encoding='utf-8') as f:
                    json.dump(data['preferences'], f, indent=2)
            
            if data.get('patterns'):
                with open(self.patterns_file, 'w', encoding='utf-8') as f:
                    json.dump(data['patterns'], f, indent=2)
            
            if data.get('strategies'):
                with open(self.strategies_file, 'w', encoding='utf-8') as f:
                    json.dump(data['strategies'], f, indent=2)
            
            print(f"Learning data imported from {import_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importing learning data: {e}")
    
    def clear_learning_data(self):
        """Remove all learned data"""
        files_to_remove = [
            self.preferences_file,
            self.patterns_file,
            self.strategies_file
        ]
        
        for filepath in files_to_remove:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Removed {filepath}")
                except OSError as e:
                    print(f"Error removing {filepath}: {e}")
        
        # Clear reflection reports
        if os.path.exists(self.reports_dir):
            for filename in os.listdir(self.reports_dir):
                filepath = os.path.join(self.reports_dir, filename)
                try:
                    os.remove(filepath)
                except OSError:
                    pass
