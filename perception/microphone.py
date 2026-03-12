import sys
import pyaudiowpatch as pyaudio

# Monkey patch: Make speech_recognition use PyAudioWPatch
sys.modules['pyaudio'] = pyaudio

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("Speech recognition not available - install with: pip install speechrecognition PyAudioWPatch")

import threading
import queue
import time

class MicrophoneInput:
    def __init__(self, config):
        self.config = config
        self.speech_queue = queue.Queue()
        self.listening = False
        self.last_speech_time = 0
        self.consecutive_short_phrases = 0
        self.last_processed_speech = ""  # Track last speech to avoid duplicates
        self.last_processed_time = 0
        
        if not SPEECH_AVAILABLE:
            print("Microphone input disabled - speech recognition not installed")
            return
        
        self.recognizer = sr.Recognizer()
        
        # Balanced thresholds for accuracy and responsiveness
        self.recognizer.energy_threshold = 500
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.2
        self.recognizer.dynamic_energy_ratio = 2.0
        
        # Speech recognition thresholds - OPTIMIZED for longer sentences
        self.recognizer.pause_threshold = 1.5  # Increased from 1.0 to allow longer sentences
        self.recognizer.phrase_threshold = 0.3  # Reduced to start capturing sooner
        self.recognizer.non_speaking_duration = 1.2  # Increased to wait longer for continuation
        
        # Conversation state
        self.in_conversation = False
        self.conversation_start_time = 0
        
        try:
            # Use Internal Microphone (device_index=1)
            self.microphone = sr.Microphone(device_index=1)
            # Adjust for ambient noise
            print("Calibrating microphone for ambient noise... (this takes 2 seconds)")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"✓ Microphone ready! Energy threshold: {self.recognizer.energy_threshold}")
        except Exception as e:
            print(f"Microphone initialization failed: {e}")
            self.microphone = None
    
    def start_listening(self):
        """Start background listening"""
        if not SPEECH_AVAILABLE or not self.microphone:
            return
        
        self.listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
    
    def _listen_loop(self):
        """Background listening loop - simplified for reliability"""
        if not self.microphone:
            return
        
        print("🎤 Listening for your voice...")
        with self.microphone as source:
            while self.listening:
                try:
                    # Skip if AI is speaking (unless user interrupts)
                    if hasattr(self, '_action_layer') and self._action_layer.speaking:
                        try:
                            audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=3)
                            self._action_layer.stop_speaking()
                            print("🛑 Interrupted by user")
                            self._process_audio(audio)
                            continue
                        except sr.WaitTimeoutError:
                            continue
                    
                    # Listen for speech with short timeout
                    audio = self.recognizer.listen(source, timeout=2.0, phrase_time_limit=5)
                    
                    # Process in background to avoid blocking
                    threading.Thread(target=self._process_audio, args=(audio,), daemon=True).start()
                    
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"Microphone error: {e}")
                    time.sleep(0.1)
    
    def _process_audio(self, audio):
        """Process audio in background thread"""
        try:
            # Set timeout for API call
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(5)
            
            text = self.recognizer.recognize_google(audio, language="en-US")
            
            # Reset timeout
            socket.setdefaulttimeout(original_timeout)
            
            # Clean and validate
            text = text.strip()
            if len(text) < 3:
                return
            
            # Skip filler words
            if text.lower() in ['uh', 'um', 'hmm']:
                return
            
            # Simple duplicate check
            current_time = time.time()
            if (current_time - self.last_processed_time) < 1.0:
                if text.lower() == self.last_processed_speech.lower():
                    return
            
            print(f"👂 You said: {text}")
            self.speech_queue.put(text)
            
            self.last_processed_speech = text
            self.last_processed_time = current_time
            self.last_speech_time = current_time
            self.in_conversation = True
            self.conversation_start_time = current_time
            
        except sr.UnknownValueError:
            pass  # Could not understand
        except sr.RequestError as e:
            print(f"⚠️ Speech recognition error: {e}")
        except Exception as e:
            print(f"⚠️ Audio processing error: {e}")
    
    def set_action_layer(self, action_layer):
        """Set reference to action layer to check if AI is speaking"""
        self._action_layer = action_layer
    
    def check_speech(self):
        """Check if user said something - returns ONLY the latest speech"""
        if not SPEECH_AVAILABLE:
            return None
        
        # Get the LATEST speech only, discard all older ones
        latest = None
        while not self.speech_queue.empty():
            try:
                latest = self.speech_queue.get_nowait()
            except:
                break
        
        return latest
    
    def clear_queue(self):
        """Clear all pending speech from queue"""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except:
                break
    
    def get_latest_speech(self):
        """Get the next speech from queue (don't skip any)"""
        if not SPEECH_AVAILABLE:
            return None
        
        try:
            return self.speech_queue.get_nowait()
        except queue.Empty:
            return None
        except Exception as e:
            print(f"⚠️ Queue error: {e}")
            return None
    
    def is_in_conversation(self):
        """Check if currently in active conversation"""
        return self.in_conversation
    
    def stop(self):
        self.listening = False
