"""
System Command Implementations
Methods for executing system control commands
"""

def add_system_command_methods(executor_class):
    """Add system control methods to CommandExecutor class"""
    
    def _open_application(self, params: dict) -> dict:
        """Open a Windows application"""
        app_name = params.get('app_name', '')
        if not app_name:
            return {'success': False, 'message': 'No application specified'}
        
        return self.system_control.open_application(app_name)
    
    def _sleep_computer(self, params: dict) -> dict:
        """Put computer to sleep"""
        return self.system_control.sleep_computer()
    
    def _shutdown_computer(self, params: dict) -> dict:
        """Shutdown computer"""
        delay = params.get('delay', 60)
        return self.system_control.shutdown_computer(delay)
    
    def _restart_computer(self, params: dict) -> dict:
        """Restart computer"""
        delay = params.get('delay', 60)
        return self.system_control.restart_computer(delay)
    
    def _lock_computer(self, params: dict) -> dict:
        """Lock computer"""
        return self.system_control.lock_computer()
    
    def _set_volume(self, params: dict) -> dict:
        """Set volume level"""
        level = params.get('level', 50)
        return self.system_control.set_volume(level)
    
    def _volume_up(self, params: dict) -> dict:
        """Increase volume"""
        increment = params.get('increment', 10)
        return self.system_control.volume_up(increment)
    
    def _volume_down(self, params: dict) -> dict:
        """Decrease volume"""
        decrement = params.get('decrement', 10)
        return self.system_control.volume_down(decrement)
    
    def _mute(self, params: dict) -> dict:
        """Mute volume"""
        return self.system_control.mute_volume()
    
    def _unmute(self, params: dict) -> dict:
        """Unmute volume"""
        return self.system_control.unmute_volume()
    
    def _set_brightness(self, params: dict) -> dict:
        """Set brightness level"""
        level = params.get('level', 50)
        return self.system_control.set_brightness(level)
    
    def _brightness_up(self, params: dict) -> dict:
        """Increase brightness"""
        increment = params.get('increment', 10)
        return self.system_control.brightness_up(increment)
    
    def _brightness_down(self, params: dict) -> dict:
        """Decrease brightness"""
        decrement = params.get('decrement', 10)
        return self.system_control.brightness_down(decrement)
    
    def _search_files(self, params: dict) -> dict:
        """Search for files"""
        query = params.get('query', '')
        if not query:
            return {'success': False, 'message': 'No search query provided'}
        
        location = params.get('location', 'C:\\')
        max_results = params.get('max_results', 10)
        
        return self.system_control.search_files(query, location, max_results)
    
    def _minimize_windows(self, params: dict) -> dict:
        """Minimize all windows"""
        return self.system_control.minimize_all_windows()
    
    # Add methods to class
    executor_class._open_application = _open_application
    executor_class._sleep_computer = _sleep_computer
    executor_class._shutdown_computer = _shutdown_computer
    executor_class._restart_computer = _restart_computer
    executor_class._lock_computer = _lock_computer
    executor_class._set_volume = _set_volume
    executor_class._volume_up = _volume_up
    executor_class._volume_down = _volume_down
    executor_class._mute = _mute
    executor_class._unmute = _unmute
    executor_class._set_brightness = _set_brightness
    executor_class._brightness_up = _brightness_up
    executor_class._brightness_down = _brightness_down
    executor_class._search_files = _search_files
    executor_class._minimize_windows = _minimize_windows
