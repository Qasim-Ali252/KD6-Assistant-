"""
Vosk-based offline speech recognition
Fast, reliable, no internet required
"""
import sys
import pyaudiowpatch as pyaudio
sys.modules['pyaudio'] = pyaudio

import threading
import queue
import time
import json

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Vosk not available - install with: pip install vosk")

class MicrophoneInputVosk:
    def __init__(self, config):
        self.config = config
        self.speech_queue = queue.Queue()
        self.listening = False
        self.paused = False  # New: pause flag for when AI is speaking
        self.last_speech_time = 0
        self.last_processed_speech = ""
        self.last_processed_time = 0
        
        if not VOSK_AVAILABLE:
            print("Vosk speech recognition not available")
            return
        
        # Load Vosk model
        model_path = config.get('perception', {}).get('vosk_model_path', 'models/vosk-model-en')
        try:
            print(f"Loading Vosk model from {model_path}...")
            self.model = Model(model_path)
            print("✓ Vosk model loaded")
        except Exception as e:
            print(f"✗ Failed to load Vosk model: {e}")
            print("  Download model from: https://alphacephei.com/vosk/models")
            self.model = None
            return
        
        # Initialize PyAudio
        self.p = pyaudio.PyAudio()
        
        # Get microphone device from config (default to 1 for internal mic)
        self.device_index = config.get('perception', {}).get('microphone_device_index', 1)
        self.sample_rate = 16000  # Vosk works best with 16kHz
        
        print(f"✓ Microphone ready (Vosk offline recognition)")
    
    def start_listening(self):
        """Start background listening"""
        if not VOSK_AVAILABLE or not self.model:
            return
        
        self.listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
    
    def _listen_loop(self):
        """Background listening loop with Vosk"""
        print("🎤 Listening for your voice (offline)...")
        
        # Create recognizer
        rec = KaldiRecognizer(self.model, self.sample_rate)
        rec.SetWords(True)
        
        # Track partial results for faster response
        last_partial = ""
        partial_stable_count = 0
        
        # Open audio stream
        stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=4000
        )
        stream.start_stream()
        
        while self.listening:
            try:
                # Skip processing if paused (AI is speaking)
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Read audio data
                data = stream.read(4000, exception_on_overflow=False)
                
                # Process with Vosk
                if rec.AcceptWaveform(data):
                    # Complete phrase recognized
                    result = json.loads(rec.Result())
                    text = result.get('text', '').strip()
                    
                    if text:
                        self._process_text(text)
                    
                    # Reset partial tracking
                    last_partial = ""
                    partial_stable_count = 0
                else:
                    # Check partial result for faster response
                    partial_result = json.loads(rec.PartialResult())
                    partial_text = partial_result.get('partial', '').strip()
                    
                    # If partial text is stable for 3 iterations and has enough words, process it
                    if partial_text and len(partial_text.split()) >= 3:
                        if partial_text == last_partial:
                            partial_stable_count += 1
                            # After 6 stable iterations (~0.75 seconds), process it
                            if partial_stable_count >= 6:
                                self._process_text(partial_text)
                                last_partial = ""
                                partial_stable_count = 0
                                rec.Reset()  # Reset recognizer for next phrase
                        else:
                            last_partial = partial_text
                            partial_stable_count = 1
                
            except Exception as e:
                print(f"Microphone error: {e}")
                time.sleep(0.1)
        
        stream.stop_stream()
        stream.close()
    
    def _process_text(self, text):
        """Process recognized text"""
        # Apply common corrections for mishearings
        text = self._apply_corrections(text)
        
        # Filter very short speech
        if len(text) < 5:
            return
        
        # Skip if only 1-2 words and they're common filler words
        words = text.lower().split()
        if len(words) <= 2:
            common_words = {'the', 'a', 'an', 'i', 'you', 'it', 'is', 'are', 'was', 'were', 'be', 'have', 'has', 'had', 'do', 'does', 'did'}
            if all(word in common_words for word in words):
                return
        
        # Skip filler words
        if text.lower() in ['uh', 'um', 'hmm', 'huh', 'the', 'yeah', 'okay', 'ok']:
            return
        
        # Skip if AI is currently speaking (don't process echo)
        if hasattr(self, '_action_layer') and self._action_layer.speaking:
            return
        
        # Simple duplicate check
        current_time = time.time()
        if (current_time - self.last_processed_time) < 2.0:
            if text.lower() == self.last_processed_speech.lower():
                return
        
        print(f"👂 You said: {text}")
        self.speech_queue.put(text)
        
        self.last_processed_speech = text
        self.last_processed_time = current_time
        self.last_speech_time = current_time
    
    def _apply_corrections(self, text):
        """Apply common speech recognition corrections"""
        corrections = {
            # KD6 variations
            'elo guarantee six': 'hello kd six',
            'the elo guarantee six': 'hello kd six',
            'guarantee six': 'kd six',
            'k d six': 'kd six',
            'k d 6': 'kd six',
            'katie six': 'kd six',
            'katy six': 'kd six',
            'k six': 'kd six',
            
            # Blockchain variations
            'blocked in': 'blockchain',
            'block in': 'blockchain',
            'blocked chain': 'blockchain',
            'block chain': 'blockchain',
            'the blood': 'blockchain',
            'blocked in the': 'blockchain',
            'block in the': 'blockchain',
            
            # Common greetings
            'elo': 'hello',
            'helo': 'hello',
            'hay': 'hey',
            
            # Add more corrections as you discover them
        }
        
        text_lower = text.lower()
        for wrong, correct in corrections.items():
            if wrong in text_lower:
                text = text_lower.replace(wrong, correct)
                break
        
        return text
    
    def set_action_layer(self, action_layer):
        """Set reference to action layer"""
        self._action_layer = action_layer
    
    def get_latest_speech(self):
        """Get next speech from queue"""
        if not VOSK_AVAILABLE:
            return None
        
        try:
            return self.speech_queue.get_nowait()
        except queue.Empty:
            return None
        except Exception as e:
            print(f"⚠️ Queue error: {e}")
            return None
    
    def clear_queue(self):
        """Clear all pending speech"""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except:
                break
    
    def pause_listening(self):
        """Pause speech recognition (when AI is speaking)"""
        self.paused = True
        print("🔇 Microphone paused")
    
    def resume_listening(self):
        """Resume speech recognition (when AI finishes speaking)"""
        time.sleep(0.5)  # Small delay to avoid catching tail end of speech
        self.paused = False
        print("🎤 Microphone resumed")
    
    def stop(self):
        self.listening = False
        if hasattr(self, 'p'):
            self.p.terminate()
