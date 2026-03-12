"""
Minimal KD6 - Just speech recognition and responses
No memory, no emotion, no reflection - just instant responses
"""
import time
from datetime import datetime
from perception.microphone_vosk import MicrophoneInputVosk
from conversation.llm import ConversationEngine
from action.output import ActionLayer
from avatar.window import AvatarWindow
from personality.layer import PersonalityLayer
from automation.command_executor import CommandExecutor
import json

class MinimalKD6:
    def __init__(self):
        print("Initializing Minimal KD6...")
        
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Only essential components
        self.microphone = MicrophoneInputVosk(self.config)
        self.conversation = ConversationEngine(self.config)
        self.action_layer = ActionLayer(self.config)
        self.personality = PersonalityLayer(self.config)
        self.command_executor = CommandExecutor(self.config)
        
        # Avatar if enabled
        if self.config.get('avatar', {}).get('enabled', False):
            self.avatar = AvatarWindow(self.config)
            self.action_layer.set_avatar(self.avatar)
        
        self.microphone.set_action_layer(self.action_layer)
        self.microphone.start_listening()
        
        print("✓ Minimal KD6 ready")
    
    def run(self):
        print("Starting main loop...")
        
        # Initial greeting
        response = {
            'text': "Hey! I'm ready to chat. This is the minimal version - super fast!",
            'emotion': 'happy',
            'trigger': 'system_started'
        }
        self.action_layer.execute(response)
        time.sleep(1)
        
        while True:
            try:
                # Get speech
                speech = self.microphone.get_latest_speech()
                
                if speech:
                    print(f"⚡ Processing: {speech}")
                    
                    # Check for automation commands FIRST
                    command_type, parameters = self.command_executor.parse_intent(speech)
                    
                    if command_type == 'cancel':
                        if self.action_layer.speaking:
                            self.action_layer.stop_speaking()
                        response = {'text': "Okay, cancelled", 'emotion': 'neutral', 'trigger': 'cancel'}
                        self.action_layer.execute(response)
                        continue
                    
                    # Execute automation command
                    if command_type:
                        print(f"🤖 Executing: {command_type}")
                        if self.action_layer.speaking:
                            self.action_layer.stop_speaking()
                        
                        result = self.command_executor.execute_command(command_type, parameters)
                        
                        if result['success']:
                            response = {'text': result['message'], 'emotion': 'neutral', 'trigger': 'automation'}
                        else:
                            response = {'text': f"Sorry, I couldn't do that. {result['message']}", 'emotion': 'concerned', 'trigger': 'automation_error'}
                        
                        self.action_layer.execute(response)
                        continue
                    
                    if command_type == 'incomplete_youtube':
                        response = {'text': "What would you like me to play on YouTube?", 'emotion': 'curious', 'trigger': 'automation_prompt'}
                        self.action_layer.execute(response)
                        continue
                    
                    # Regular conversation
                    # Minimal context
                    context = {
                        'user_speech': speech,
                        'time': datetime.now().strftime('%H:%M'),
                        'hour': datetime.now().hour,
                        'user_present': True,
                        'mood': 'neutral',
                        'recent_memory': [],
                        'user_preferences': {},
                        'state_changes': []
                    }
                    
                    # Minimal emotion
                    emotion = {'emotion': 'neutral', 'intensity': 0.5}
                    
                    # Generate response
                    response = self.conversation.generate(
                        context=context,
                        emotion=emotion,
                        personality=self.personality,
                        memory=None,
                        trigger='user_spoke',
                        preference_profile=None,
                        activity=None
                    )
                    
                    # Speak
                    self.action_layer.execute(response)
                
                time.sleep(0.01)  # Very fast loop
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(0.1)
    
    def cleanup(self):
        self.microphone.stop()
        self.action_layer.cleanup()
        if hasattr(self, 'avatar'):
            self.avatar.cleanup()

if __name__ == "__main__":
    kd6 = MinimalKD6()
    try:
        kd6.run()
    finally:
        kd6.cleanup()
