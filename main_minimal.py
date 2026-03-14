"""
Minimal KD6 - Just speech recognition and responses
No memory, no emotion, no reflection - just instant responses
"""
import time
from datetime import datetime
from conversation.llm import ConversationEngine
from action.output import ActionLayer
from avatar.window import AvatarWindow
from personality.layer import PersonalityLayer
from automation.command_executor import CommandExecutor
import json

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, env vars must be set manually

def load_microphone(config):
    """Load microphone based on speech_recognition setting in config"""
    engine = config.get('perception', {}).get('speech_recognition', 'vosk')
    if engine == 'whisper':
        from perception.microphone_whisper import MicrophoneInputWhisper
        print("🎙 Using Groq Whisper speech recognition")
        return MicrophoneInputWhisper(config)
    else:
        from perception.microphone_vosk import MicrophoneInputVosk
        print("🎙 Using Vosk speech recognition")
        return MicrophoneInputVosk(config)

class MinimalKD6:
    def __init__(self):
        print("Initializing Minimal KD6...")
        
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Only essential components
        self.microphone = load_microphone(self.config)
        self.conversation = ConversationEngine(self.config)
        self.action_layer = ActionLayer(self.config)
        self.personality = PersonalityLayer(self.config)
        self.command_executor = CommandExecutor(self.config)
        
        # Avatar if enabled
        if self.config.get('avatar', {}).get('enabled', False):
            self.avatar = AvatarWindow(self.config)
            self.action_layer.set_avatar(self.avatar)
        
        # Connect microphone and action layer
        self.microphone.set_action_layer(self.action_layer)
        self.action_layer.set_microphone(self.microphone)
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
                    start_time = time.time()
                    print(f"⚡ Processing: {speech}")
                    
                    # Check for automation commands FIRST
                    t1 = time.time()
                    command_type, parameters = self.command_executor.parse_intent(speech)
                    print(f"⏱️ Command parsing: {(time.time() - t1)*1000:.0f}ms")
                    
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
                    t2 = time.time()
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
                    print(f"⏱️ Context building: {(time.time() - t2)*1000:.0f}ms")
                    
                    # Generate response
                    t3 = time.time()
                    response = self.conversation.generate(
                        context=context,
                        emotion=emotion,
                        personality=self.personality,
                        memory=None,
                        trigger='user_spoke',
                        preference_profile=None,
                        activity=None
                    )
                    print(f"⏱️ LLM generation: {(time.time() - t3)*1000:.0f}ms")
                    
                    # Speak
                    t4 = time.time()
                    self.action_layer.execute(response)
                    print(f"⏱️ TTS queue: {(time.time() - t4)*1000:.0f}ms")
                    
                    print(f"⏱️ TOTAL: {(time.time() - start_time)*1000:.0f}ms")
                
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
