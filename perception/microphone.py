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
        """Background listening loop with improved detection"""
        if not self.microphone:
            return
        
        print("🎤 Listening for your voice...")
        with self.microphone as source:
            while self.listening:
                try:
                    # Skip if AI is currently speaking (unless user wants to interrupt)
                    if hasattr(self, '_action_layer') and self._action_layer.speaking:
                        # Check for interrupt - listen with very short timeout
                        try:
                            audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=3)
                            # User is trying to interrupt
                            self._action_layer.stop_speaking()
                            print("🛑 Interrupted by user")
                            text = self.recognizer.recognize_google(audio)
                            print(f"👂 You said: {text}")
                            self.speech_queue.put(text)
                            self.in_conversation = True
                            self.conversation_start_time = time.time()
                            continue
                        except (sr.WaitTimeoutError, sr.UnknownValueError):
                            continue
                    
                    # Adaptive timeout based on conversation state
                    timeout = 1.0 if self.in_conversation else 3.0
                    phrase_limit = 20  # Allow longer phrases
                    
                    # Listen for speech
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                    
                    # Get audio duration to filter very short captures
                    audio_duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                    
                    # Skip very short audio (less than 0.8 seconds)
                    if audio_duration < 0.8:
                        continue
                    
                    # Try Google Speech Recognition with language hint
                    try:
                        text = self.recognizer.recognize_google(
                            audio,
                            language="en-US",
                            show_all=False
                        )
                        
                        # Clean up the text
                        text = text.strip()
                        
                        # Filter out very short accidental captures
                        if len(text) < 5:  # Increased from 3 to 5
                            continue
                        
                        # Filter out common misrecognitions
                        ignore_phrases = ['uh', 'um', 'hmm', 'mhm', 'uh-huh', 'okay', 'ok']
                        if text.lower() in ignore_phrases:
                            continue
                        
                        # Count words - skip if too few words for a command
                        word_count = len(text.split())
                        if word_count < 2:  # Need at least 2 words for meaningful command
                            continue
                        
                        # Check for duplicate/similar speech within 2 seconds (reduced from 3)
                        current_time = time.time()
                        if (current_time - self.last_processed_time) < 2.0:
                            # Check if this is very similar to last speech
                            if text.lower() == self.last_processed_speech.lower():
                                continue  # Skip exact duplicate
                            
                            # Check if this is a CONTINUATION (starts where last one ended)
                            # If so, COMBINE them instead of filtering
                            if self.last_processed_speech and not text.lower().startswith(self.last_processed_speech.lower()):
                                # This might be a continuation - combine them
                                combined = self.last_processed_speech + " " + text
                                print(f"🔗 Combined speech: {combined}")
                                text = combined
                        
                        print(f"👂 You said: {text}")
                        self.speech_queue.put(text)
                        
                        # Update tracking
                        self.last_processed_speech = text
                        self.last_processed_time = current_time
                        
                        # Update conversation state
                        self.last_speech_time = time.time()
                        self.in_conversation = True
                        self.conversation_start_time = time.time()
                        
                    except sr.UnknownValueError:
                        # Could not understand - don't show message, just continue
                        continue
                    except sr.RequestError as e:
                        print(f"⚠️  Speech recognition service error: {e}")
                        continue
                    
                except sr.WaitTimeoutError:
                    # Check if conversation has ended (no speech for 30 seconds)
                    if self.in_conversation and (time.time() - self.last_speech_time) > 30:
                        self.in_conversation = False
                        self.consecutive_short_phrases = 0
                        self.recognizer.pause_threshold = 1.5
                    continue
                except sr.UnknownValueError:
                    # Could not understand audio
                    continue
                except Exception as e:
                    print(f"Microphone error: {e}")
    
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
        """Get only the most recent speech, discarding older ones"""
        if not SPEECH_AVAILABLE:
            return None
        
        latest = None
        while not self.speech_queue.empty():
            try:
                latest = self.speech_queue.get_nowait()
            except:
                break
        return latest
    
    def is_in_conversation(self):
        """Check if currently in active conversation"""
        return self.in_conversation
    
    def stop(self):
        self.listening = False
