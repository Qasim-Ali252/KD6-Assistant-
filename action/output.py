import threading
import queue
import time

try:
    import win32com.client
    SAPI_AVAILABLE = True
except ImportError:
    SAPI_AVAILABLE = False
    print("Warning: pywin32 not installed. Install with: pip install pywin32")

class ActionLayer:
    def __init__(self, config):
        self.config = config
        self.tts_provider = config['api']['tts_provider']
        self.avatar = None  # Will be set by main.py
        self.speaker = None  # SAPI speaker object
        self.current_speech = None
        
        if not SAPI_AVAILABLE:
            print("TTS disabled - pywin32 not available")
            return
        
        # Initialize local TTS engine in a dedicated thread
        self.tts_queue = queue.Queue()
        self.speaking = False
        self.stop_requested = False
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        print("TTS worker thread started")
    
    def _tts_worker(self):
        """Dedicated TTS worker thread using Windows SAPI"""
        try:
            # Create SAPI speaker
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Get available voices
            voices = self.speaker.GetVoices()
            
            # Use female voice if available (usually index 1)
            if voices.Count > 1:
                self.speaker.Voice = voices.Item(1)
            
            # Set rate (range: -10 to 10, default: 0)
            self.speaker.Rate = 1
            
            print("TTS engine initialized (Windows SAPI)")
            
            while True:
                text = self.tts_queue.get()
                if text is None:  # Shutdown signal
                    break
                
                try:
                    print(f"🔊 Speaking: {text[:50]}...")
                    self.speaking = True
                    self.stop_requested = False
                    self.current_speech = text
                    
                    # Speak with interrupt check
                    # Use SPF_ASYNC flag to allow interruption
                    self.speaker.Speak(text, 1)  # 1 = SVSFlagsAsync
                    
                    # Wait for speech to complete or be interrupted
                    while self.speaker.Status.RunningState == 2:  # 2 = SRSEIsSpeaking
                        if self.stop_requested:
                            self.speaker.Speak("", 3)  # 3 = SVSFPurgeBeforeSpeak | SVSFlagsAsync
                            break
                        time.sleep(0.1)
                    
                    self.speaking = False
                    self.current_speech = None
                    
                    if not self.stop_requested:
                        print("✅ Finished speaking")
                    else:
                        print("🛑 Speech interrupted")
                        
                except Exception as e:
                    print(f"TTS error in worker: {e}")
                    self.speaking = False
                    self.current_speech = None
        except Exception as e:
            print(f"TTS worker initialization error: {e}")
    
    def stop_speaking(self):
        """Stop current speech (for interrupts)"""
        if self.speaking:
            self.stop_requested = True
            if self.speaker:
                try:
                    self.speaker.Speak("", 3)  # Purge and stop
                except:
                    pass
    
    def execute(self, response):
        """Execute AI action - speak and animate"""
        if not SAPI_AVAILABLE:
            return
        
        text = response['text']
        emotion = response['emotion']
        
        print(f"\n[{emotion.upper()}] KD6: {text}")
        
        # Update avatar state
        if self.avatar:
            self.avatar.set_emotion(emotion)
            self.avatar.set_state('speaking')
        
        # Queue speech for TTS worker
        self.tts_queue.put(text)
        
        # TODO: Trigger avatar animation
    
    def set_avatar(self, avatar):
        """Set reference to avatar window"""
        self.avatar = avatar
    
    def cleanup(self):
        if SAPI_AVAILABLE:
            self.tts_queue.put(None)  # Signal shutdown
            self.tts_thread.join(timeout=2)
