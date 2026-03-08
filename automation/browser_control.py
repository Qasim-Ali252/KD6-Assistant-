"""
Browser Control Module
Controls web browser for automation tasks
"""
import webbrowser
import time
import subprocess
from typing import Optional

# Try to import pyautogui, but make it optional
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    pyautogui = None

class BrowserController:
    """Controls browser automation"""
    
    def __init__(self, config):
        self.config = config
        self.browser_path = config.get('automation', {}).get('browser_path', 'chrome')
        
        # Set pyautogui safety settings if available
        if PYAUTOGUI_AVAILABLE:
            pyautogui.PAUSE = 0.5  # Pause between actions
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    
    def open_browser(self):
        """Open Chrome browser"""
        try:
            # Try to open Chrome
            if self.browser_path == 'chrome':
                subprocess.Popen(['chrome'])
            else:
                subprocess.Popen([self.browser_path])
            time.sleep(2)  # Wait for browser to open
            return True
        except Exception as e:
            print(f"Error opening browser: {e}")
            return False
    
    def open_new_tab(self):
        """Open new tab in browser"""
        if not PYAUTOGUI_AVAILABLE:
            print("PyAutoGUI not available - cannot open new tab")
            return False
        
        try:
            pyautogui.hotkey('ctrl', 't')
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Error opening new tab: {e}")
            return False
    
    def open_url(self, url: str):
        """Open a specific URL"""
        try:
            webbrowser.open(url)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Error opening URL: {e}")
            return False
    
    def search_youtube(self, query: str):
        """Search YouTube and play first result"""
        try:
            # Strategy 1: Try to open direct video URL if pyautogui available
            # Strategy 2: Open search results (fallback)
            
            if PYAUTOGUI_AVAILABLE:
                # Get screen size for dynamic positioning
                screen_width, screen_height = pyautogui.size()
                
                # Get click position from config or use defaults
                x_percent = self.config.get('automation', {}).get('youtube_click_x_percent', 0.25)
                y_percent = self.config.get('automation', {}).get('youtube_click_y_percent', 0.30)
                load_delay = self.config.get('automation', {}).get('youtube_load_delay', 4)
                
                # Calculate click position based on screen size
                click_x = int(screen_width * x_percent)
                click_y = int(screen_height * y_percent)
                
                # Open YouTube search
                youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                webbrowser.open(youtube_url)
                print(f"🌐 Opened YouTube search: {query}")
                
                # Wait for page to load
                time.sleep(load_delay)
                
                # Click first video at calculated position
                print(f"🖱️ Clicking at position ({click_x}, {click_y}) on {screen_width}x{screen_height} screen")
                pyautogui.click(click_x, click_y)
                print("✓ Clicked first video")
                
                # Small delay to ensure click registered
                time.sleep(0.5)
            else:
                # Fallback: Open search results without auto-click
                youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                webbrowser.open(youtube_url)
                print("Note: Opened search results. Install pyautogui for auto-play: pip install pyautogui")
            
            return True
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return False
    
    def type_text(self, text: str):
        """Type text into active field"""
        if not PYAUTOGUI_AVAILABLE:
            print("PyAutoGUI not available - cannot type text")
            return False
        
        try:
            pyautogui.write(text, interval=0.05)
            return True
        except Exception as e:
            print(f"Error typing text: {e}")
            return False
    
    def press_enter(self):
        """Press Enter key"""
        if not PYAUTOGUI_AVAILABLE:
            print("PyAutoGUI not available - cannot press enter")
            return False
        
        try:
            pyautogui.press('enter')
            return True
        except Exception as e:
            print(f"Error pressing enter: {e}")
            return False
    
    def search_google(self, query: str):
        """Search Google"""
        try:
            google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(google_url)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Error searching Google: {e}")
            return False
