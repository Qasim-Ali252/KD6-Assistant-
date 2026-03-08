import time
import json
import uuid
from datetime import datetime
from perception.camera import CameraPerception
from perception.microphone import MicrophoneInput
from context.builder import ContextBuilder
from memory.manager import MemoryManager
from memory.preference_learner import PreferenceLearner
from memory.reflection import ReflectionModule
from emotion.engine import EmotionEngine
from personality.layer import PersonalityLayer
from decision.engine import DecisionEngine
from conversation.llm import ConversationEngine
from action.output import ActionLayer
from avatar.window import AvatarWindow
from automation.command_executor import CommandExecutor
from utils.logger import setup_logger

logger = setup_logger()

class KD6Companion:
    def __init__(self, config_path="config.json"):
        logger.info("Initializing KD6 AI Companion...")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.camera = CameraPerception(self.config)
        self.microphone = MicrophoneInput(self.config)
        self.microphone.start_listening()  # Start listening for voice input
        self.context_builder = ContextBuilder(self.config)
        self.memory = MemoryManager(self.config)
        self.emotion_engine = EmotionEngine(self.config)
        self.personality = PersonalityLayer(self.config)
        self.decision_engine = DecisionEngine(self.config)
        self.conversation = ConversationEngine(self.config)
        self.action_layer = ActionLayer(self.config)
        self.command_executor = CommandExecutor(self.config)
        
        # Connect memory manager to conversation engine
        self.conversation.load_user_info(self.memory)
        
        # Initialize intelligence modules
        self.preference_learner = PreferenceLearner(self.config)
        self.reflection_module = ReflectionModule(self.config)
        
        # Load learning data
        self._load_learning_data()
        
        # Initialize avatar window if enabled
        if self.config.get('avatar', {}).get('enabled', False):
            self.avatar = AvatarWindow(self.config)
            self.action_layer.set_avatar(self.avatar)
        else:
            self.avatar = None
        
        # Link microphone to action layer to prevent echo
        self.microphone.set_action_layer(self.action_layer)
        
        self.running = False
        self.conversation_start_time = None
        self.just_started = True  # Flag to prevent duplicate greetings
        self.last_reminder_check = time.time()
        logger.info("KD6 initialized successfully")
    
    def _load_learning_data(self):
        """Load persisted learning data on startup"""
        # Load preferences
        pref_data = self.memory.load_preference_data()
        if pref_data:
            logger.info("Loaded preference data")
        
        # Load patterns
        pattern_data = self.memory.load_patterns()
        if pattern_data:
            logger.info(f"Loaded {len(pattern_data.get('patterns', []))} patterns")
        
        # Load strategies
        strategy_data = self.memory.load_strategies()
        if strategy_data:
            logger.info(f"Loaded {len(strategy_data.get('strategies', []))} strategies")
    
    def _save_learning_data(self):
        """Save learning data on shutdown"""
        # Get current preferences
        preferences = self.preference_learner.get_preferences()
        self.memory.store_preference_data(preferences)
        
        # Save patterns
        self.memory.store_patterns(self.preference_learner.patterns)
        
        # Save strategies
        self.memory.store_strategies(self.reflection_module.strategies)
        
        # Save session statistics
        session_stats = self.emotion_engine.get_session_statistics()
        self.memory.store_fact('last_session_stats', session_stats)
        
        logger.info("Learning data saved")
    
    def run(self):
        """Main autonomous loop with optimized response time"""
        self.running = True
        logger.info("Starting main loop...")
        
        # Initial greeting when system starts
        initial_greeting = self.conversation.generate(
            context={
                'time': datetime.now().strftime('%H:%M'),
                'hour': datetime.now().hour,
                'user_present': True,
                'user_speech': None,
                'state_changes': ['system_started']
            },
            emotion={'emotion': 'happy', 'intensity': 0.7},
            personality=self.personality,
            memory=self.memory,
            trigger='system_started',
            preference_profile=None,
            activity=None
        )
        
        # Speak initial greeting
        self.action_layer.execute(initial_greeting)
        logger.info("Initial greeting delivered")
        
        # Wait for greeting to finish before starting main loop
        time.sleep(1)
        
        try:
            while self.running:
                # 1. PRIORITY CHECK: Get latest speech FIRST (discard old speech)
                latest_speech = self.microphone.get_latest_speech()
                
                # 2. FAST PATH: Check for automation commands IMMEDIATELY
                if latest_speech:
                    print(f"⚡ Processing: {latest_speech}")  # Visual feedback
                    command_type, parameters = self.command_executor.parse_intent(latest_speech)
                    
                    # Handle cancellation
                    if command_type == 'cancel':
                        logger.info("User cancelled command")
                        if self.action_layer.speaking:
                            self.action_layer.stop_speaking()
                        response = {
                            'text': "Okay, cancelled",
                            'emotion': 'neutral',
                            'trigger': 'cancel'
                        }
                        self.action_layer.execute(response)
                        continue
                    
                    # Execute automation commands with HIGHEST PRIORITY
                    if command_type:
                        logger.info(f"Executing automation command: {command_type}")
                        
                        # Stop any ongoing speech immediately
                        if self.action_layer.speaking:
                            self.action_layer.stop_speaking()
                        
                        # Execute command
                        result = self.command_executor.execute_command(command_type, parameters)
                        
                        # Quick response
                        if result['success']:
                            response = {
                                'text': result['message'],
                                'emotion': 'neutral',
                                'trigger': 'automation_command'
                            }
                        else:
                            response = {
                                'text': f"Sorry, I couldn't do that. {result['message']}",
                                'emotion': 'concerned',
                                'trigger': 'automation_error'
                            }
                        
                        # Speak response
                        self.action_layer.execute(response)
                        
                        # Update memory
                        context = {'user_speech': latest_speech, 'time': datetime.now().strftime('%H:%M')}
                        self.memory.add_interaction(context, response)
                        
                        # Continue to next loop iteration immediately
                        continue
                    
                    # Handle incomplete YouTube command
                    if command_type == 'incomplete_youtube':
                        response = {
                            'text': "What would you like me to play on YouTube?",
                            'emotion': 'curious',
                            'trigger': 'automation_prompt'
                        }
                        self.action_layer.execute(response)
                        continue
                
                # 3. NORMAL PATH: Regular perception and conversation
                perception_data = {
                    'camera': self.camera.get_perception(),
                    'audio': latest_speech  # Use the speech we already got
                }
                
                # Build context
                context = self.context_builder.build(perception_data, self.memory)
                
                # Update emotion state
                emotion = self.emotion_engine.update(context)
                
                # Get emotion history for activity inference
                emotion_history = self.emotion_engine.get_emotion_history(time_window=300)
                
                # Infer activity
                activity = self.decision_engine.infer_activity(emotion_history)
                
                # Decision - should AI respond?
                decision = self.decision_engine.evaluate(context, emotion, self.memory)
                
                # Skip user_entered trigger right after startup
                if self.just_started and decision.get('reason') == 'user_entered':
                    self.just_started = False
                    decision = {'should_respond': False}
                elif decision['should_respond']:
                    self.just_started = False
                
                # Check for proactive triggers (only if not speaking)
                if not decision['should_respond'] and self.config['decision']['proactive_enabled']:
                    if not self.action_layer.speaking:
                        trigger_decision = self.decision_engine.evaluate_triggers(context, emotion_history)
                        if trigger_decision:
                            decision = {
                                'should_respond': True,
                                'reason': trigger_decision.trigger_type,
                                'trigger_context': trigger_decision.context
                            }
                            self.decision_engine.record_trigger_fired(trigger_decision.trigger_type)
                
                if decision['should_respond']:
                    logger.info(f"Decision: {decision['reason']}")
                    
                    # Get preference profile
                    preference_profile = self.preference_learner.get_preferences()
                    
                    # Get active strategies
                    active_strategies = self.reflection_module.get_active_strategies()
                    
                    # Generate conversation ID for tracking
                    conversation_id = str(uuid.uuid4())
                    self.conversation_start_time = time.time()
                    
                    # Generate response with enhanced context
                    response = self.conversation.generate(
                        context=context,
                        emotion=emotion,
                        personality=self.personality,
                        memory=self.memory,
                        trigger=decision['reason'],
                        preference_profile=preference_profile,
                        activity=activity
                    )
                    
                    # Track conversation for reflection
                    self.reflection_module.track_conversation(
                        conversation_id=conversation_id,
                        trigger_type=decision['reason'],
                        topic='general',
                        ai_message=response['text']
                    )
                    
                    # Execute action (speak + animate)
                    self.action_layer.execute(response)
                    
                    # Update memory
                    self.memory.add_interaction(context, response)
                    
                    # Wait for user response if this was a proactive conversation
                    if decision['reason'] != 'user_spoke':
                        # Monitor for user response
                        self._monitor_user_response(conversation_id, decision['reason'])
                
                # Check for idle reflection
                if self.reflection_module.check_idle_reflection():
                    logger.info("Performing idle reflection...")
                    report = self.reflection_module.perform_idle_reflection()
                    self.memory.store_reflection_report(report)
                    logger.info(f"Reflection complete: {len(report.strategies)} new strategies")
                
                # Check for deep reflection (overnight)
                current_hour = datetime.now().hour
                if current_hour == self.config['reflection']['deep_reflection_hour']:
                    if self.reflection_module.last_deep_reflection is None or \
                       (datetime.now() - self.reflection_module.last_deep_reflection).days >= 1:
                        logger.info("Performing deep reflection...")
                        report = self.reflection_module.perform_deep_reflection()
                        self.memory.store_reflection_report(report)
                        logger.info(f"Deep reflection complete")
                
                # Check for task reminders
                if self.config.get('automation', {}).get('task_reminders_enabled', True):
                    now = time.time()
                    if now - self.last_reminder_check >= self.config.get('automation', {}).get('check_reminders_interval', 60):
                        self.last_reminder_check = now
                        self._check_task_reminders()
                
                time.sleep(0.05)  # Reduced from 0.1 to 0.05 for faster response
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.shutdown()
    
    def _monitor_user_response(self, conversation_id: str, trigger_type: str):
        """Monitor for user response to proactive conversation"""
        start_time = time.time()
        timeout = 120  # 2 minutes
        
        while time.time() - start_time < timeout:
            # Check for speech
            speech = self.microphone.check_speech()
            if speech:
                response_time = time.time() - self.conversation_start_time
                
                # Record response in reflection module
                self.reflection_module.record_user_response(speech, response_time)
                
                # Record interaction in preference learner
                engagement = 'engaged' if response_time < 30 else 'neutral'
                self.preference_learner.record_interaction(
                    trigger_type=trigger_type,
                    topic='general',
                    user_response=speech,
                    engagement=engagement,
                    response_time=response_time
                )
                
                return
            
            time.sleep(0.5)
        
        # No response - record as ignored
        response_time = time.time() - self.conversation_start_time
        self.reflection_module.record_user_response(None, response_time)
        self.preference_learner.record_interaction(
            trigger_type=trigger_type,
            topic='general',
            user_response=None,
            engagement='ignored',
            response_time=response_time
        )
    
    def _check_task_reminders(self):
        """Check for due task reminders and notify user"""
        overdue_tasks = self.command_executor.task_manager.get_overdue_tasks()
        
        if overdue_tasks:
            # Get the most recent overdue task
            task = overdue_tasks[0]
            
            # Create reminder notification
            response = {
                'text': f"Reminder: {task.title.replace('Reminder: ', '')}",
                'emotion': 'neutral',
                'trigger': 'task_reminder'
            }
            
            # Speak the reminder
            self.action_layer.execute(response)
            
            # Mark as completed so it doesn't repeat
            self.command_executor.task_manager.complete_task(task.task_id)
            
            logger.info(f"Delivered reminder: {task.title}")
    
    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        
        # Save learning data
        self._save_learning_data()
        
        self.camera.release()
        self.microphone.stop()
        self.action_layer.cleanup()
        if self.avatar:
            self.avatar.cleanup()
        logger.info("KD6 shut down successfully")
    
    def export_data(self, export_path: str):
        """Export all learning data"""
        self.memory.export_learning_data(export_path)
    
    def import_data(self, import_path: str):
        """Import learning data"""
        self.memory.import_learning_data(import_path)
        self._load_learning_data()
    
    def clear_data(self):
        """Clear all learning data"""
        self.memory.clear_learning_data()
        logger.info("All learning data cleared")

if __name__ == "__main__":
    companion = KD6Companion()
    companion.run()
