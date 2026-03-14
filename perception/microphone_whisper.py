"""
Groq Whisper-based speech recognition
Much more accurate than Vosk, uses your existing Groq API key
"""
import sys
import pyaudiowpatch as pyaudio
sys.modules['pyaudio'] = pyaudio

import threading
import queue
import time
import wave
import io
import tempfile
import os

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Groq not available - install with: pip install groq")


class MicrophoneInputWhisper:
    def __init__(self, config):
        self.config = config
        self.speech_queue = queue.Queue()
        self.listening = False
        self.paused = False
        self.last_processed_speech = ""
        self.last_processed_time = 0
        self._action_layer = None
        self.client = None
        self.p = None

        if not GROQ_AVAILABLE:
            print("Groq Whisper not available - install with: pip install groq")
            return

        # Read API key from env first, fallback to config
        api_key = os.environ.get('GROQ_API_KEY') or config.get('api', {}).get('groq_api_key', '')
        if not api_key or api_key == 'YOUR_GROQ_API_KEY':
            print("✗ No Groq API key found - set GROQ_API_KEY in .env")
            return

        self.client = Groq(api_key=api_key)
        self.p = pyaudio.PyAudio()
        self.device_index = config.get('perception', {}).get('microphone_device_index', None)
        self.sample_rate = 16000
        self.chunk_duration = config.get('perception', {}).get('whisper_chunk_seconds', 4)
        self.silence_threshold = config.get('perception', {}).get('silence_threshold', 500)

        print("✓ Microphone ready (Groq Whisper recognition)")

    def start_listening(self):
        if not self.client:
            return
        self.listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

    def _listen_loop(self):
        print("🎤 Listening for your voice (Groq Whisper)...")

        frames_per_chunk = int(self.sample_rate * self.chunk_duration)

        stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=1024
        )
        stream.start_stream()

        try:
            while self.listening:
                if self.paused:
                    # Drain the stream while paused so no echo builds up
                    stream.read(1024, exception_on_overflow=False)
                    time.sleep(0.05)
                    continue

                # Collect audio chunk
                frames = []
                chunk_paused = False
                for _ in range(0, frames_per_chunk // 1024):
                    if not self.listening:
                        break
                    if self.paused:
                        chunk_paused = True
                        break
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)

                # Discard chunk if we got paused mid-recording (contains TTS echo)
                if chunk_paused or not frames:
                    continue

                audio_data = b''.join(frames)
                if not self._has_speech(audio_data):
                    continue

                # Send to Groq Whisper in background thread
                threading.Thread(
                    target=self._transcribe,
                    args=(audio_data,),
                    daemon=True
                ).start()

        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass

    def _has_speech(self, audio_data: bytes) -> bool:
        """Check if audio contains speech above silence threshold"""
        import struct
        samples = struct.unpack(f'{len(audio_data)//2}h', audio_data)
        max_amplitude = max(abs(s) for s in samples)
        return max_amplitude > self.silence_threshold

    def _transcribe(self, audio_data: bytes):
        """Send audio to Groq Whisper API"""
        try:
            # Write to temp wav file (Groq needs a file)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
                with wave.open(tmp_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data)

            with open(tmp_path, 'rb') as f:
                result = self.client.audio.transcriptions.create(
                    file=('audio.wav', f, 'audio/wav'),
                    model='whisper-large-v3-turbo',
                    language='en',
                    response_format='text'
                )

            os.unlink(tmp_path)

            text = result.strip() if isinstance(result, str) else result.text.strip()
            if text:
                self._process_text(text)

        except Exception as e:
            print(f"Whisper transcription error: {e}")
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _process_text(self, text: str):
        # Filter filler/noise
        if len(text) < 3:
            return
        if text.lower() in ['you', 'uh', 'um', 'hmm', 'huh', 'yeah', 'okay', 'ok', 'the', 'thanks']:
            return

        if self._action_layer and self._action_layer.speaking:
            return

        current_time = time.time()
        if (current_time - self.last_processed_time) < 2.0:
            if text.lower() == self.last_processed_speech.lower():
                return

        print(f"👂 You said: {text}")
        self.speech_queue.put(text)
        self.last_processed_speech = text
        self.last_processed_time = current_time

    def set_action_layer(self, action_layer):
        self._action_layer = action_layer

    def get_latest_speech(self):
        try:
            return self.speech_queue.get_nowait()
        except queue.Empty:
            return None

    def clear_queue(self):
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except:
                break

    def pause_listening(self):
        self.paused = True
        print("🔇 Microphone paused")

    def resume_listening(self):
        def _resume():
            time.sleep(1.2)  # Wait longer to clear TTS echo
            self.paused = False
            print("🎤 Microphone resumed")
        threading.Thread(target=_resume, daemon=True).start()

    def stop(self):
        self.listening = False
        if self.p:
            self.p.terminate()
