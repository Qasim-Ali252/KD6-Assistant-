import pygame
from pygame.locals import *
import threading
import queue
import os
import time
import numpy as np

try:
    from avatar.vtube_studio import VTubeStudioAPI
    VTUBE_AVAILABLE = True
except ImportError:
    VTUBE_AVAILABLE = False

class AvatarWindow:
    def __init__(self, config):
        self.config = config
        self.running = False
        self.state = 'idle'
        self.emotion = 'neutral'
        
        # Window settings
        avatar_config = config.get('avatar', {})
        self.width = avatar_config.get('window_width', 800)
        self.height = avatar_config.get('window_height', 600)
        self.use_vtube = avatar_config.get('use_vtube_studio', True)
        
        # VTube Studio API
        self.vtube = None
        if self.use_vtube and VTUBE_AVAILABLE:
            try:
                self.vtube = VTubeStudioAPI(config)
                print("✓ VTube Studio API initialized")
            except Exception as e:
                print(f"✗ VTube Studio init failed: {e}")
        
        # Animation state
        self.mouth_open = 0.0
        self.mouth_phase = 0.0
        
        # Command queue
        self.command_queue = queue.Queue()
        
        # Start window thread
        self.window_thread = threading.Thread(target=self._run_window, daemon=True)
        self.window_thread.start()
    
    def _run_window(self):
        """Run status window"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("KD6 - VTube Studio Controller")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        print("✓ Controller window opened")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            while not self.command_queue.empty():
                cmd = self.command_queue.get()
                self._process_command(cmd)
            
            self._update_animations()
            self._render()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
    
    def _process_command(self, cmd):
        """Process commands"""
        cmd_type = cmd.get('type')
        
        if cmd_type == 'set_state':
            new_state = cmd.get('state', 'idle')
            if new_state != self.state:
                print(f"🎭 State changed: {self.state} → {new_state}")
            self.state = new_state
        elif cmd_type == 'set_emotion':
            self.emotion = cmd.get('emotion', 'neutral')
            if self.vtube:
                self.vtube.set_emotion(self.emotion)
        elif cmd_type == 'set_mouth':
            self.mouth_open = cmd.get('value', 0.0)
    
    def _update_animations(self):
        """Update animations"""
        if self.state == 'speaking':
            self.mouth_phase += 0.3
            self.mouth_open = (np.sin(self.mouth_phase) + 1) / 2
            
            # Send to VTube Studio every frame when speaking
            if self.vtube and self.vtube.connected and self.vtube.authenticated:
                self.vtube.set_mouth_open(self.mouth_open)
        else:
            # Gradually close mouth
            if self.mouth_open > 0:
                self.mouth_open = max(0, self.mouth_open - 0.05)
                if self.vtube and self.vtube.connected and self.vtube.authenticated:
                    self.vtube.set_mouth_open(self.mouth_open)
            
            self.mouth_phase = 0
    
    def _render(self):
        """Render status display"""
        # Dark background
        self.screen.fill((20, 20, 30))
        
        # Title
        font_title = pygame.font.Font(None, 64)
        title = font_title.render("KD6 Controller", True, (100, 200, 255))
        title_rect = title.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title, title_rect)
        
        # VTube Studio status
        font_normal = pygame.font.Font(None, 36)
        
        if self.vtube and self.vtube.connected:
            status_color = (100, 255, 150)
            status_text = "✓ Connected to VTube Studio"
            
            if self.vtube.current_model:
                model_name = self.vtube.current_model.get('modelName', 'Unknown')
                model_text = font_normal.render(f"Model: {model_name}", True, (200, 200, 200))
                self.screen.blit(model_text, (50, 200))
        else:
            status_color = (255, 100, 100)
            status_text = "✗ Not connected to VTube Studio"
        
        status = font_normal.render(status_text, True, status_color)
        self.screen.blit(status, (50, 150))
        
        # State indicator
        state_colors = {
            'idle': (100, 200, 255),
            'speaking': (255, 200, 100),
            'listening': (100, 255, 150),
            'thinking': (200, 150, 255)
        }
        state_color = state_colors.get(self.state, (255, 255, 255))
        
        pygame.draw.circle(self.screen, state_color, (50, 280), 20)
        state_text = font_normal.render(f"State: {self.state.upper()}", True, state_color)
        self.screen.blit(state_text, (90, 265))
        
        # Emotion
        emotion_text = font_normal.render(f"Emotion: {self.emotion}", True, (200, 200, 200))
        self.screen.blit(emotion_text, (50, 330))
        
        # Mouth indicator
        if self.state == 'speaking':
            mouth_width = int(300 * self.mouth_open)
            pygame.draw.rect(self.screen, (255, 200, 100), 
                           (50, 400, mouth_width, 20))
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (50, 400, 300, 20), 2)
            
            mouth_label = font_normal.render("Mouth Open", True, (200, 200, 200))
            self.screen.blit(mouth_label, (50, 370))
        
        # Instructions
        font_small = pygame.font.Font(None, 28)
        instructions = [
            "Instructions:",
            "1. Open VTube Studio",
            "2. Load your Allium model",
            "3. Enable API in Settings",
            "4. KD6 will control the avatar automatically"
        ]
        
        y = 480
        for line in instructions:
            text = font_small.render(line, True, (150, 150, 150))
            self.screen.blit(text, (50, y))
            y += 30
    
    def set_state(self, state):
        """Set avatar state"""
        print(f"🎭 Avatar state: {state}")
        self.command_queue.put({'type': 'set_state', 'state': state})
    
    def set_emotion(self, emotion):
        """Set avatar emotion"""
        self.command_queue.put({'type': 'set_emotion', 'emotion': emotion})
    
    def set_mouth_open(self, value):
        """Set mouth open amount"""
        self.command_queue.put({'type': 'set_mouth', 'value': value})
    
    def cleanup(self):
        """Cleanup"""
        self.running = False
        if self.vtube:
            self.vtube.cleanup()
        self.window_thread.join(timeout=2)
