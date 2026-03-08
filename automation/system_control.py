"""
Windows System Control Module
Allows KD6 to control Windows OS features and applications
"""
import subprocess
import os
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import time
from typing import Optional, List, Dict

# Try to import Windows-specific modules
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠ pycaw not available - install with: pip install pycaw")

try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except ImportError:
    BRIGHTNESS_AVAILABLE = False
    print("⚠ screen-brightness-control not available - install with: pip install screen-brightness-control")

class WindowsSystemControl:
    """Controls Windows system features"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize audio control if available
        if AUDIO_AVAILABLE:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            except Exception as e:
                print(f"⚠ Audio control initialization failed: {e}")
                self.volume = None
        else:
            self.volume = None
        
        # Common Windows applications
        self.applications = {
            'calculator': 'calc.exe',
            'notepad': 'notepad.exe',
            'paint': 'mspaint.exe',
            'file explorer': 'explorer.exe',
            'task manager': 'taskmgr.exe',
            'control panel': 'control.exe',
            'settings': 'ms-settings:',
            'command prompt': 'cmd.exe',
            'powershell': 'powershell.exe',
            'snipping tool': 'SnippingTool.exe',
            'magnifier': 'magnify.exe',
            'on-screen keyboard': 'osk.exe',
            'character map': 'charmap.exe',
            'disk cleanup': 'cleanmgr.exe',
            'registry editor': 'regedit.exe',
            'system information': 'msinfo32.exe',
            'resource monitor': 'resmon.exe',
            'device manager': 'devmgmt.msc',
            'disk management': 'diskmgmt.msc',
            'services': 'services.msc',
            'event viewer': 'eventvwr.msc'
        }
    
    # ==================== APPLICATION CONTROL ====================
    
    def open_application(self, app_name: str) -> Dict:
        """
        Open a Windows application
        
        Args:
            app_name: Name of application (e.g., 'calculator', 'notepad')
            
        Returns:
            Result dictionary
        """
        app_name_lower = app_name.lower()
        
        if app_name_lower in self.applications:
            try:
                command = self.applications[app_name_lower]
                subprocess.Popen(command, shell=True)
                print(f"✓ Opened {app_name}")
                return {
                    'success': True,
                    'message': f'Opened {app_name}'
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Failed to open {app_name}: {e}'
                }
        else:
            return {
                'success': False,
                'message': f'Unknown application: {app_name}'
            }
    
    # ==================== SYSTEM CONTROL ====================
    
    def sleep_computer(self) -> Dict:
        """Put computer to sleep"""
        try:
            print("💤 Putting computer to sleep...")
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], check=True)
            return {
                'success': True,
                'message': 'Putting computer to sleep'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to sleep computer: {e}'
            }
    
    def shutdown_computer(self, delay_seconds: int = 60) -> Dict:
        """
        Shutdown computer with optional delay
        
        Args:
            delay_seconds: Seconds to wait before shutdown (default: 60)
        """
        try:
            print(f"🔌 Shutting down in {delay_seconds} seconds...")
            subprocess.run(['shutdown', '/s', '/t', str(delay_seconds)], check=True)
            return {
                'success': True,
                'message': f'Computer will shutdown in {delay_seconds} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to shutdown: {e}'
            }
    
    def restart_computer(self, delay_seconds: int = 60) -> Dict:
        """
        Restart computer with optional delay
        
        Args:
            delay_seconds: Seconds to wait before restart (default: 60)
        """
        try:
            print(f"🔄 Restarting in {delay_seconds} seconds...")
            subprocess.run(['shutdown', '/r', '/t', str(delay_seconds)], check=True)
            return {
                'success': True,
                'message': f'Computer will restart in {delay_seconds} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to restart: {e}'
            }
    
    def cancel_shutdown(self) -> Dict:
        """Cancel pending shutdown/restart"""
        try:
            subprocess.run(['shutdown', '/a'], check=True)
            print("✓ Cancelled shutdown/restart")
            return {
                'success': True,
                'message': 'Cancelled shutdown/restart'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to cancel: {e}'
            }
    
    def lock_computer(self) -> Dict:
        """Lock the computer"""
        try:
            print("🔒 Locking computer...")
            ctypes.windll.user32.LockWorkStation()
            return {
                'success': True,
                'message': 'Locking computer'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to lock: {e}'
            }
    
    # ==================== VOLUME CONTROL ====================
    
    def set_volume(self, level: int) -> Dict:
        """
        Set system volume
        
        Args:
            level: Volume level (0-100)
        """
        if not AUDIO_AVAILABLE or not self.volume:
            return {
                'success': False,
                'message': 'Audio control not available. Install pycaw: pip install pycaw'
            }
        
        try:
            # Convert 0-100 to 0.0-1.0
            volume_scalar = max(0, min(100, level)) / 100.0
            self.volume.SetMasterVolumeLevelScalar(volume_scalar, None)
            print(f"🔊 Volume set to {level}%")
            return {
                'success': True,
                'message': f'Volume set to {level}%'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to set volume: {e}'
            }
    
    def get_volume(self) -> Dict:
        """Get current system volume"""
        if not AUDIO_AVAILABLE or not self.volume:
            return {
                'success': False,
                'message': 'Audio control not available'
            }
        
        try:
            current_volume = int(self.volume.GetMasterVolumeLevelScalar() * 100)
            return {
                'success': True,
                'volume': current_volume,
                'message': f'Current volume: {current_volume}%'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to get volume: {e}'
            }
    
    def mute_volume(self) -> Dict:
        """Mute system volume"""
        if not AUDIO_AVAILABLE or not self.volume:
            return {
                'success': False,
                'message': 'Audio control not available'
            }
        
        try:
            self.volume.SetMute(1, None)
            print("🔇 Volume muted")
            return {
                'success': True,
                'message': 'Volume muted'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to mute: {e}'
            }
    
    def unmute_volume(self) -> Dict:
        """Unmute system volume"""
        if not AUDIO_AVAILABLE or not self.volume:
            return {
                'success': False,
                'message': 'Audio control not available'
            }
        
        try:
            self.volume.SetMute(0, None)
            print("🔊 Volume unmuted")
            return {
                'success': True,
                'message': 'Volume unmuted'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to unmute: {e}'
            }
    
    def volume_up(self, increment: int = 10) -> Dict:
        """Increase volume by increment"""
        current = self.get_volume()
        if current['success']:
            new_level = min(100, current['volume'] + increment)
            return self.set_volume(new_level)
        return current
    
    def volume_down(self, decrement: int = 10) -> Dict:
        """Decrease volume by decrement"""
        current = self.get_volume()
        if current['success']:
            new_level = max(0, current['volume'] - decrement)
            return self.set_volume(new_level)
        return current
    
    # ==================== BRIGHTNESS CONTROL ====================
    
    def set_brightness(self, level: int) -> Dict:
        """
        Set screen brightness
        
        Args:
            level: Brightness level (0-100)
        """
        if not BRIGHTNESS_AVAILABLE:
            return {
                'success': False,
                'message': 'Brightness control not available. Install with: pip install screen-brightness-control'
            }
        
        try:
            level = max(0, min(100, level))
            sbc.set_brightness(level)
            print(f"💡 Brightness set to {level}%")
            return {
                'success': True,
                'message': f'Brightness set to {level}%'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to set brightness: {e}'
            }
    
    def get_brightness(self) -> Dict:
        """Get current screen brightness"""
        if not BRIGHTNESS_AVAILABLE:
            return {
                'success': False,
                'message': 'Brightness control not available'
            }
        
        try:
            current_brightness = sbc.get_brightness()[0]
            return {
                'success': True,
                'brightness': current_brightness,
                'message': f'Current brightness: {current_brightness}%'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to get brightness: {e}'
            }
    
    def brightness_up(self, increment: int = 10) -> Dict:
        """Increase brightness by increment"""
        current = self.get_brightness()
        if current['success']:
            new_level = min(100, current['brightness'] + increment)
            return self.set_brightness(new_level)
        return current
    
    def brightness_down(self, decrement: int = 10) -> Dict:
        """Decrease brightness by decrement"""
        current = self.get_brightness()
        if current['success']:
            new_level = max(0, current['brightness'] - decrement)
            return self.set_brightness(new_level)
        return current
    
    # ==================== FILE SEARCH ====================
    
    def search_files(self, query: str, location: str = "C:\\", max_results: int = 10) -> Dict:
        """
        Search for files on the system
        
        Args:
            query: Search query (filename or pattern)
            location: Starting directory (default: C:\\)
            max_results: Maximum number of results
        """
        try:
            print(f"🔍 Searching for '{query}' in {location}...")
            results = []
            
            # Use Windows search command
            command = f'dir /s /b "{location}*{query}*" 2>nul'
            output = subprocess.check_output(command, shell=True, text=True, timeout=10)
            
            files = output.strip().split('\n')
            results = [f for f in files if f][:max_results]
            
            if results:
                print(f"✓ Found {len(results)} file(s)")
                return {
                    'success': True,
                    'results': results,
                    'count': len(results),
                    'message': f'Found {len(results)} file(s) matching "{query}"'
                }
            else:
                return {
                    'success': True,
                    'results': [],
                    'count': 0,
                    'message': f'No files found matching "{query}"'
                }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'Search timed out (too many files)'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Search failed: {e}'
            }
    
    def open_file_location(self, filepath: str) -> Dict:
        """Open file location in Explorer"""
        try:
            subprocess.run(['explorer', '/select,', filepath], check=True)
            return {
                'success': True,
                'message': f'Opened location of {os.path.basename(filepath)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to open location: {e}'
            }
    
    # ==================== WINDOW MANAGEMENT ====================
    
    def minimize_all_windows(self) -> Dict:
        """Minimize all windows (show desktop)"""
        try:
            # Windows key + D
            import pyautogui
            pyautogui.hotkey('win', 'd')
            print("📉 Minimized all windows")
            return {
                'success': True,
                'message': 'Minimized all windows'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to minimize windows: {e}'
            }
    
    def get_available_applications(self) -> List[str]:
        """Get list of available applications"""
        return list(self.applications.keys())
