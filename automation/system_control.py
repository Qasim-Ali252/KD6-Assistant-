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
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL
                from ctypes import cast, POINTER
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            except AttributeError:
                # Newer pycaw API
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    self.volume = AudioUtilities.GetSpeakers().QueryInterface(IAudioEndpointVolume)
                except Exception as e:
                    print(f"⚠ Audio control unavailable: {e}")
                    self.volume = None
            except Exception as e:
                print(f"⚠ Audio control unavailable: {e}")
                self.volume = None
        else:
            self.volume = None
        
        # Common Windows applications
        self.applications = {
            # Built-in Windows tools
            'calculator':       {'exe': 'calc.exe'},
            'notepad':          {'exe': 'notepad.exe'},
            'paint':            {'exe': 'mspaint.exe'},
            'file explorer':    {'exe': 'explorer.exe'},
            'task manager':     {'exe': 'taskmgr.exe'},
            'control panel':    {'exe': 'control.exe'},
            'settings':         {'exe': 'ms-settings:',   'protocol': True},
            'command prompt':   {'exe': 'cmd.exe'},
            'powershell':       {'exe': 'powershell.exe'},
            'snipping tool':    {'exe': 'SnippingTool.exe'},
            'registry editor':  {'exe': 'regedit.exe'},
            'device manager':   {'exe': 'devmgmt.msc'},
            'disk management':  {'exe': 'diskmgmt.msc'},
            'services':         {'exe': 'services.msc'},
            # Desktop apps (in PATH or common locations)
            'vscode':           {'exe': 'code'},
            'vs code':          {'exe': 'code'},
            'visual studio code': {'exe': 'code'},
            'chrome':           {'exe': 'chrome'},
            'google chrome':    {'exe': 'chrome'},
            'firefox':          {'exe': 'firefox'},
            'edge':             {'exe': 'msedge'},
            'microsoft edge':   {'exe': 'msedge'},
            'vlc':              {'exe': 'vlc'},
            'notepad++':        {'exe': 'notepad++'},
            'winrar':           {'exe': 'winrar'},
            '7zip':             {'exe': '7zfm'},
            'pycharm':          {'exe': 'pycharm64'},
            'git bash':         {'exe': 'git-bash'},
            'obs':              {'exe': 'obs64'},
            'obs studio':       {'exe': 'obs64'},
            'word':             {'exe': 'winword'},
            'microsoft word':   {'exe': 'winword'},
            'excel':            {'exe': 'excel'},
            'microsoft excel':  {'exe': 'excel'},
            'powerpoint':       {'exe': 'powerpnt'},
            'microsoft powerpoint': {'exe': 'powerpnt'},
            'outlook':          {'exe': 'outlook'},
            'microsoft outlook': {'exe': 'outlook'},
            # UWP/Store apps - use protocol, fallback to web
            'whatsapp':   {'protocol': 'whatsapp:',    'url': 'https://web.whatsapp.com'},
            'spotify':    {'protocol': 'spotify:',     'url': 'https://open.spotify.com'},
            'discord':    {'protocol': 'discord:',     'url': 'https://discord.com/app'},
            'telegram':   {'protocol': 'tg:',          'url': 'https://web.telegram.org'},
            'steam':      {'protocol': 'steam:',       'url': 'https://store.steampowered.com'},
            'skype':      {'protocol': 'skype:',       'url': 'https://web.skype.com'},
            'teams':      {'protocol': 'msteams:',     'url': 'https://teams.microsoft.com'},
            'microsoft teams': {'protocol': 'msteams:', 'url': 'https://teams.microsoft.com'},
            'zoom':       {'protocol': 'zoommtg:',     'url': 'https://zoom.us/join'},
            'netflix':    {'protocol': 'netflix:',     'url': 'https://www.netflix.com'},
            'instagram':  {'protocol': 'instagram:',   'url': 'https://www.instagram.com'},
            'tiktok':     {'protocol': 'tiktok:',      'url': 'https://www.tiktok.com'},
            'snapchat':   {'protocol': 'snapchat:',    'url': 'https://web.snapchat.com'},
            'linkedin':   {'protocol': 'linkedin:',    'url': 'https://www.linkedin.com'},
            'pinterest':  {'protocol': 'pinterest:',   'url': 'https://www.pinterest.com'},
            # Web-only apps
            'facebook':   {'url': 'https://www.facebook.com'},
            'twitter':    {'url': 'https://www.twitter.com'},
            'x':          {'url': 'https://www.x.com'},
            'youtube':    {'url': 'https://www.youtube.com'},
            'gmail':      {'url': 'https://mail.google.com'},
            'google':     {'url': 'https://www.google.com'},
            'reddit':     {'url': 'https://www.reddit.com'},
            'github':     {'url': 'https://www.github.com'},
            'amazon':     {'url': 'https://www.amazon.com'},
            'twitch':     {'url': 'https://www.twitch.tv'},
        }
    
    # ==================== APPLICATION CONTROL ====================
    
    def open_application(self, app_name: str) -> Dict:
        """Open app - tries installed app first, falls back to browser"""
        import shutil
        import winreg

        app_name_lower = app_name.lower().strip()

        # Find entry
        entry = self.applications.get(app_name_lower)
        if not entry:
            for key, val in self.applications.items():
                if key in app_name_lower or app_name_lower in key:
                    entry = val
                    app_name = key
                    break

        if not entry:
            return {'success': False, 'message': f'Unknown application: {app_name}'}

        exe = entry.get('exe')
        protocol = entry.get('protocol')
        url = entry.get('url')

        try:
            # 1. Try exe/command if defined
            if exe:
                # Check if it's a protocol (like ms-settings:)
                if entry.get('protocol') is True:
                    subprocess.Popen(f'start {exe}', shell=True)
                    print(f"✓ Opened {app_name}")
                    return {'success': True, 'message': f'Opening {app_name}'}

                # Check if exe is in PATH
                if shutil.which(exe) or shutil.which(exe + '.exe'):
                    subprocess.Popen(exe, shell=True)
                    print(f"✓ Opened {app_name}")
                    return {'success': True, 'message': f'Opening {app_name}'}

                # Try running anyway (might be in a custom PATH location)
                try:
                    result = subprocess.run(f'where {exe}', shell=True, capture_output=True, timeout=3)
                    if result.returncode == 0:
                        subprocess.Popen(exe, shell=True)
                        print(f"✓ Opened {app_name}")
                        return {'success': True, 'message': f'Opening {app_name}'}
                except Exception:
                    pass

            # 2. Try protocol (UWP/Store apps like whatsapp:, spotify:)
            if protocol:
                try:
                    # Check if protocol is registered in Windows registry
                    reg_path = f'SOFTWARE\\Classes\\{protocol.rstrip(":")}'
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    subprocess.Popen(f'start {protocol}', shell=True)
                    print(f"✓ Opened {app_name} via app")
                    return {'success': True, 'message': f'Opening {app_name}'}
                except FileNotFoundError:
                    # Protocol not registered - app not installed, fall through to browser
                    pass
                except Exception:
                    # Try anyway
                    subprocess.Popen(f'start {protocol}', shell=True)
                    print(f"✓ Opened {app_name} via protocol")
                    return {'success': True, 'message': f'Opening {app_name}'}

            # 3. Fallback to browser
            if url:
                subprocess.Popen(f'start {url}', shell=True)
                print(f"✓ Opened {app_name} in browser")
                return {'success': True, 'message': f'Opening {app_name} in browser'}

            return {'success': False, 'message': f'Could not open {app_name}'}

        except Exception as e:
            return {'success': False, 'message': f'Failed to open {app_name}: {e}'}
    
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

    # ==================== CLOSE APPLICATION ====================

    def close_application(self, app_name: str) -> Dict:
        """Close a running application by name"""
        # Map friendly names to process names
        process_map = {
            'chrome': 'chrome.exe', 'google chrome': 'chrome.exe',
            'firefox': 'firefox.exe', 'edge': 'msedge.exe',
            'microsoft edge': 'msedge.exe', 'notepad': 'notepad.exe',
            'notepad++': 'notepad++.exe', 'vlc': 'vlc.exe',
            'spotify': 'Spotify.exe', 'discord': 'Discord.exe',
            'steam': 'steam.exe', 'telegram': 'Telegram.exe',
            'whatsapp': 'WhatsApp.exe', 'zoom': 'Zoom.exe',
            'teams': 'Teams.exe', 'skype': 'Skype.exe',
            'obs': 'obs64.exe', 'obs studio': 'obs64.exe',
            'word': 'WINWORD.EXE', 'excel': 'EXCEL.EXE',
            'powerpoint': 'POWERPNT.EXE', 'outlook': 'OUTLOOK.EXE',
            'vscode': 'Code.exe', 'vs code': 'Code.exe',
            'pycharm': 'pycharm64.exe', 'explorer': 'explorer.exe',
            'file explorer': 'explorer.exe', 'paint': 'mspaint.exe',
            'calculator': 'Calculator.exe', 'task manager': 'Taskmgr.exe',
        }
        app_lower = app_name.lower().strip()
        process = process_map.get(app_lower, app_name)
        try:
            result = subprocess.run(f'taskkill /F /IM "{process}"', shell=True,
                                    capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ Closed {app_name}")
                return {'success': True, 'message': f'Closed {app_name}'}
            else:
                # Try partial match
                result2 = subprocess.run(f'taskkill /F /FI "IMAGENAME eq *{app_lower}*"',
                                         shell=True, capture_output=True, text=True)
                if result2.returncode == 0:
                    return {'success': True, 'message': f'Closed {app_name}'}
                return {'success': False, 'message': f'{app_name} is not running'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to close {app_name}: {e}'}

    def close_active_window(self) -> Dict:
        """Close the currently active window"""
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            return {'success': True, 'message': 'Closed active window'}
        except Exception as e:
            return {'success': False, 'message': f'Failed: {e}'}

    def close_active_tab(self) -> Dict:
        """Close the current browser tab"""
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'w')
            return {'success': True, 'message': 'Closed active tab'}
        except Exception as e:
            return {'success': False, 'message': f'Failed: {e}'}

    # ==================== FILE EXPLORER ====================

    def open_folder(self, path: str) -> Dict:
        """Open a specific folder in File Explorer"""
        try:
            # Expand common shortcuts
            path = path.strip()
            shortcuts = {
                'desktop': os.path.join(os.path.expanduser('~'), 'Desktop'),
                'downloads': os.path.join(os.path.expanduser('~'), 'Downloads'),
                'documents': os.path.join(os.path.expanduser('~'), 'Documents'),
                'pictures': os.path.join(os.path.expanduser('~'), 'Pictures'),
                'music': os.path.join(os.path.expanduser('~'), 'Music'),
                'videos': os.path.join(os.path.expanduser('~'), 'Videos'),
                'this pc': 'shell:MyComputerFolder',
                'my pc': 'shell:MyComputerFolder',
                'c drive': 'C:\\', 'c:': 'C:\\',
                'd drive': 'D:\\', 'd:': 'D:\\',
                'e drive': 'E:\\', 'e:': 'E:\\',
            }
            resolved = shortcuts.get(path.lower(), path)
            subprocess.Popen(f'explorer "{resolved}"', shell=True)
            print(f"✓ Opened folder: {resolved}")
            return {'success': True, 'message': f'Opened {path}'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to open folder: {e}'}

    def open_file(self, filepath: str) -> Dict:
        """Open a specific file with its default application"""
        try:
            os.startfile(filepath)
            print(f"✓ Opened file: {filepath}")
            return {'success': True, 'message': f'Opened {os.path.basename(filepath)}'}
        except FileNotFoundError:
            return {'success': False, 'message': f'File not found: {filepath}'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to open file: {e}'}

    def search_and_open(self, query: str, drives: list = None) -> Dict:
        """Search for a file/folder across drives and open it"""
        if drives is None:
            drives = ['C:\\', 'D:\\', 'E:\\']
        try:
            for drive in drives:
                if not os.path.exists(drive):
                    continue
                cmd = f'dir /s /b "{drive}*{query}*" 2>nul'
                out = subprocess.check_output(cmd, shell=True, text=True, timeout=8)
                results = [r for r in out.strip().split('\n') if r]
                if results:
                    target = results[0].strip()
                    if os.path.isdir(target):
                        subprocess.Popen(f'explorer "{target}"', shell=True)
                    else:
                        os.startfile(target)
                    return {'success': True, 'message': f'Opened {os.path.basename(target)}'}
            return {'success': False, 'message': f'Could not find "{query}"'}
        except Exception as e:
            return {'success': False, 'message': f'Search failed: {e}'}

    # ==================== SETTINGS / CONNECTIVITY ====================

    def toggle_wifi(self, enable: bool) -> Dict:
        """Enable or disable WiFi"""
        try:
            action = 'enable' if enable else 'disable'
            subprocess.run(
                f'netsh interface set interface "Wi-Fi" {action}',
                shell=True, capture_output=True
            )
            state = 'enabled' if enable else 'disabled'
            print(f"✓ WiFi {state}")
            return {'success': True, 'message': f'WiFi {state}'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to toggle WiFi: {e}'}

    def toggle_bluetooth(self, enable: bool) -> Dict:
        """Enable or disable Bluetooth via Settings"""
        try:
            # Open Bluetooth settings page
            subprocess.Popen('start ms-settings:bluetooth', shell=True)
            state = 'on' if enable else 'off'
            return {'success': True, 'message': f'Opened Bluetooth settings - toggle it {state}'}
        except Exception as e:
            return {'success': False, 'message': f'Failed: {e}'}

    def open_settings(self, page: str = '') -> Dict:
        """Open Windows Settings, optionally to a specific page"""
        pages = {
            'wifi': 'ms-settings:network-wifi',
            'bluetooth': 'ms-settings:bluetooth',
            'display': 'ms-settings:display',
            'sound': 'ms-settings:sound',
            'notifications': 'ms-settings:notifications',
            'battery': 'ms-settings:batterysaver',
            'storage': 'ms-settings:storagesense',
            'apps': 'ms-settings:appsfeatures',
            'startup': 'ms-settings:startupapps',
            'privacy': 'ms-settings:privacy',
            'update': 'ms-settings:windowsupdate',
            'accounts': 'ms-settings:accounts',
            'time': 'ms-settings:dateandtime',
            'language': 'ms-settings:regionlanguage',
            'mouse': 'ms-settings:mousetouchpad',
            'keyboard': 'ms-settings:typing',
            'camera': 'ms-settings:camera',
            'microphone': 'ms-settings:privacy-microphone',
            'vpn': 'ms-settings:network-vpn',
            'airplane': 'ms-settings:network-airplanemode',
            'hotspot': 'ms-settings:network-mobilehotspot',
            'night light': 'ms-settings:display',
            'themes': 'ms-settings:themes',
            'taskbar': 'ms-settings:taskbar',
            'default apps': 'ms-settings:defaultapps',
        }
        uri = pages.get(page.lower(), 'ms-settings:')
        try:
            subprocess.Popen(f'start {uri}', shell=True)
            label = page if page else 'Settings'
            print(f"✓ Opened {label} settings")
            return {'success': True, 'message': f'Opened {label} settings'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to open settings: {e}'}

    def take_screenshot(self) -> Dict:
        """Take a screenshot and save to Desktop"""
        try:
            import pyautogui
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            from datetime import datetime
            filename = f'screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            path = os.path.join(desktop, filename)
            screenshot = pyautogui.screenshot()
            screenshot.save(path)
            print(f"✓ Screenshot saved: {filename}")
            return {'success': True, 'message': f'Screenshot saved to Desktop as {filename}'}
        except Exception as e:
            return {'success': False, 'message': f'Screenshot failed: {e}'}

    def get_battery_status(self) -> Dict:
        """Get battery percentage and charging status"""
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                pct = int(battery.percent)
                charging = 'charging' if battery.power_plugged else 'not charging'
                return {'success': True, 'message': f'Battery is at {pct}%, {charging}'}
            return {'success': False, 'message': 'No battery detected'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to get battery: {e}'}

    def empty_recycle_bin(self) -> Dict:
        """Empty the recycle bin"""
        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            return {'success': True, 'message': 'Recycle bin emptied'}
        except ImportError:
            subprocess.run('PowerShell -Command "Clear-RecycleBin -Force"', shell=True)
            return {'success': True, 'message': 'Recycle bin emptied'}
        except Exception as e:
            return {'success': False, 'message': f'Failed: {e}'}

    def new_browser_tab(self) -> Dict:
        """Open a new tab in the active browser"""
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 't')
            return {'success': True, 'message': 'Opened new tab'}
        except Exception as e:
            return {'success': False, 'message': f'Failed: {e}'}

    def maximize_window(self) -> Dict:
        """Maximize the active window"""
        try:
            import pyautogui
            pyautogui.hotkey('win', 'up')
            return {'success': True, 'message': 'Window maximized'}
        except Exception as e:
            return {'success': False, 'message': f'Failed: {e}'}

    def switch_window(self) -> Dict:
        """Switch to next window (Alt+Tab)"""
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'tab')
            return {'success': True, 'message': 'Switched window'}
        except Exception as e:
            return {'success': False, 'message': f'Failed: {e}'}

