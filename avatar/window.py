import pygame
import threading
import queue
import os
from PIL import Image
from avatar.live2d_loader import Live2DModel

class AvatarWindow:
    def __init__(self, config):
        self.config = config
        self.running = False
        self.state = 'idle'  # idle, speaking, listening, thinking
        self.emotion = 'neutral'
        
        # Window settings
        avatar_config = config.get('avatar', {})
        self.width = avatar_config.get('window_width', 800)
        self.height = avatar_config.get('window_height', 600)
        self.model_path = avatar_config.get('model_path', '')
        self.model_type = avatar_config.get('model_type', 'image')
        self.scale = avatar_config.get('scale', 1.0)
        
        # Live2D model
        self.live2d_model = None
        
        # Animation state
        self.mouth_open = 0.0  # 0.0 to 1.0
        self.blink_timer = 0
        self.current_expression = 'neutral'
        
        # Command queue for thread-safe updates
        self.command_queue = queue.Queue()
        
        # Start window in separate thread
        self.window_thread = threading.Thread(target=self._run_window, daemon=True)
        self.window_thread.start()
    
    def _run_window(self):
        """Run pygame window in dedicated thread"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("KD6 - Allium Avatar (Live2D)")
        
        # Load Live2D model or fallback to image
        self.avatar_image = None
        
        if self.model_type == 'live2d' and self.model_path.endswith('.model3.json'):
            try:
                self.live2d_model = Live2DModel(self.model_path)
                print(f"Live2D model loaded successfully")
                print(f"Available expressions: {self.live2d_model.get_expression_names()}")
                
                # Load the main texture or preview image
                preview_path = self.config.get('avatar', {}).get('preview_image', '')
                if preview_path and os.path.exists(preview_path):
                    # Use preview image if available
                    img = pygame.image.load(preview_path)
                    img_rect = img.get_rect()
                    scale_factor = min(self.width / img_rect.width, self.height / img_rect.height) * self.scale
                    new_size = (int(img_rect.width * scale_factor), int(img_rect.height * scale_factor))
                    self.avatar_image = pygame.transform.scale(img, new_size)
                    print(f"Loaded preview image: {preview_path}")
                else:
                    # Fallback to texture
                    texture_path = self.live2d_model.get_texture_path(0)
                    if texture_path and os.path.exists(texture_path):
                        img = pygame.image.load(texture_path)
                        img_rect = img.get_rect()
                        scale_factor = min(self.width / img_rect.width, self.height / img_rect.height) * self.scale
                        new_size = (int(img_rect.width * scale_factor), int(img_rect.height * scale_factor))
                        self.avatar_image = pygame.transform.scale(img, new_size)
                        print(f"Loaded texture: {texture_path}")
            except Exception as e:
                print(f"Failed to load Live2D model: {e}")
                print("Falling back to image mode")
        
        # Fallback: load as regular image
        if not self.avatar_image and os.path.exists(self.model_path):
            try:
                img = pygame.image.load(self.model_path)
                img_rect = img.get_rect()
                scale_factor = min(self.width / img_rect.width, self.height / img_rect.height) * self.scale
                new_size = (int(img_rect.width * scale_factor), int(img_rect.height * scale_factor))
                self.avatar_image = pygame.transform.scale(img, new_size)
                print(f"Loaded avatar image: {self.model_path}")
            except Exception as e:
                print(f"Failed to load avatar image: {e}")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        print("Avatar window opened")
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # Process commands from main thread
            while not self.command_queue.empty():
                cmd = self.command_queue.get()
                self._process_command(cmd)
            
            # Update animations
            self._update_animations()
            
            # Render avatar
            self._render()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
    
    def _process_command(self, cmd):
        """Process commands from main thread"""
        cmd_type = cmd.get('type')
        
        if cmd_type == 'set_state':
            self.state = cmd.get('state', 'idle')
        elif cmd_type == 'set_emotion':
            self.emotion = cmd.get('emotion', 'neutral')
        elif cmd_type == 'set_mouth':
            self.mouth_open = cmd.get('value', 0.0)
    
    def _update_animations(self):
        """Update animation states"""
        # Animate mouth when speaking
        if self.state == 'speaking':
            # Simple mouth animation
            self.mouth_open = (self.mouth_open + 0.3) % 1.0
        else:
            # Close mouth gradually
            self.mouth_open = max(0, self.mouth_open - 0.1)
        
        # Blink animation
        self.blink_timer += 1
        if self.blink_timer > 180:  # Blink every 3 seconds
            self.blink_timer = 0
    
    def _render(self):
        """Render the avatar"""
        # Clear screen with gradient background
        for y in range(self.height):
            color_value = int(20 + (y / self.height) * 40)
            pygame.draw.line(self.screen, (color_value, color_value, color_value + 10), (0, y), (self.width, y))
        
        # Draw avatar image if loaded
        if self.avatar_image:
            img_rect = self.avatar_image.get_rect()
            img_rect.center = (self.width // 2, self.height // 2)
            self.screen.blit(self.avatar_image, img_rect)
        
        # Draw status overlay
        font_small = pygame.font.Font(None, 32)
        font_large = pygame.font.Font(None, 48)
        
        # State indicator
        state_colors = {
            'idle': (100, 200, 255),
            'speaking': (255, 200, 100),
            'listening': (100, 255, 150),
            'thinking': (200, 150, 255)
        }
        state_color = state_colors.get(self.state, (255, 255, 255))
        
        # Draw state dot
        pygame.draw.circle(self.screen, state_color, (30, 30), 12)
        
        # Draw state text
        state_text = font_small.render(self.state.upper(), True, state_color)
        self.screen.blit(state_text, (50, 18))
        
        # Draw emotion
        emotion_text = font_small.render(f"Emotion: {self.emotion}", True, (200, 200, 200))
        self.screen.blit(emotion_text, (self.width - 250, 18))
        
        # Draw KD6 name at bottom
        name_text = font_large.render("KD6", True, (150, 200, 255))
        name_rect = name_text.get_rect()
        name_rect.centerx = self.width // 2
        name_rect.bottom = self.height - 20
        self.screen.blit(name_text, name_rect)
    
    def set_state(self, state):
        """Set avatar state (idle, speaking, listening, thinking)"""
        self.command_queue.put({'type': 'set_state', 'state': state})
    
    def set_emotion(self, emotion):
        """Set avatar emotion"""
        self.command_queue.put({'type': 'set_emotion', 'emotion': emotion})
    
    def set_mouth_open(self, value):
        """Set mouth open amount (0.0 to 1.0)"""
        self.command_queue.put({'type': 'set_mouth', 'value': value})
    
    def cleanup(self):
        """Close the window"""
        self.running = False
        self.window_thread.join(timeout=2)
