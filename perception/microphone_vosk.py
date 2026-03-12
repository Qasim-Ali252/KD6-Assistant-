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
        
        # Use Internal Microphone (device_index=1)
        self.device_index = 1
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
                # Read audio data
                data = stream.read(4000, exception_on_overflow=False)
                
                # Process with Vosk (always process, don't skip)
                if rec.AcceptWaveform(data):
                    # Complete phrase recognized
                    result = json.loads(rec.Result())
                    text = result.get('text', '').strip()
                    
                    if text:
                        # Check if AI is speaking - if so, it's an interrupt
                        if hasattr(self, '_action_layer') and self._action_layer.speaking:
                            self._action_layer.stop_speaking()
                            print("🛑 Interrupted by user")
                        
                        self._process_text(text)
                
            except Exception as e:
                print(f"Microphone error: {e}")
                time.sleep(0.1)
        
        stream.stop_stream()
        stream.close()
    
    def _process_text(self, text):
        """Process recognized text"""
        # Filter short speech
        if len(text) < 3:
            return
        
        # Skip filler words
        if text.lower() in ['uh', 'um', 'hmm', 'huh']:
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
    
    def stop(self):
        self.listening = False
        if hasattr(self, 'p'):
            self.p.terminate()
