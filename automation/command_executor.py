"""
Command Executor Module
Executes automation commands based on user intent
"""
from automation.browser_control import BrowserController
from automation.task_manager import TaskManager
from automation.system_control import WindowsSystemControl
from datetime import datetime, timedelta
from typing import Optional
import re
import time

class CommandExecutor:
    """Executes automation commands"""
    
    def __init__(self, config):
        self.config = config
        self.browser = BrowserController(config)
        self.task_manager = TaskManager(config)
        self.system_control = WindowsSystemControl(config)
        
        # Context tracking for multi-turn commands
        self.last_command_type = None
        self.last_command_time = 0
        self.waiting_for_query = False
    
    def execute_command(self, command_type: str, parameters: dict) -> dict:
        """
        Execute a command
        
        Args:
            command_type: Type of command
            parameters: Command parameters
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            # Browser commands
            if command_type == 'play_youtube':
                return self._play_youtube(parameters)
            elif command_type == 'search_google':
                return self._search_google(parameters)
            elif command_type == 'open_website':
                return self._open_website(parameters)
            
            # Task commands
            elif command_type == 'add_task':
                return self._add_task(parameters)
            elif command_type == 'list_tasks':
                return self._list_tasks(parameters)
            elif command_type == 'complete_task':
                return self._complete_task(parameters)
            elif command_type == 'add_reminder':
                return self._add_reminder(parameters)
            
            # System control commands
            elif command_type == 'open_application':
                return self._open_application(parameters)
            elif command_type == 'sleep_computer':
                return self._sleep_computer(parameters)
            elif command_type == 'shutdown_computer':
                return self._shutdown_computer(parameters)
            elif command_type == 'restart_computer':
                return self._restart_computer(parameters)
            elif command_type == 'lock_computer':
                return self._lock_computer(parameters)
            elif command_type == 'set_volume':
                return self._set_volume(parameters)
            elif command_type == 'volume_up':
                return self._volume_up(parameters)
            elif command_type == 'volume_down':
                return self._volume_down(parameters)
            elif command_type == 'mute':
                return self._mute(parameters)
            elif command_type == 'unmute':
                return self._unmute(parameters)
            elif command_type == 'set_brightness':
                return self._set_brightness(parameters)
            elif command_type == 'brightness_up':
                return self._brightness_up(parameters)
            elif command_type == 'brightness_down':
                return self._brightness_down(parameters)
            elif command_type == 'search_files':
                return self._search_files(parameters)
            elif command_type == 'minimize_windows':
                return self._minimize_windows(parameters)
            
            else:
                return {'success': False, 'message': f'Unknown command: {command_type}'}
        except Exception as e:
            return {'success': False, 'message': f'Error executing command: {e}'}
    
    def _play_youtube(self, params: dict) -> dict:
        """Play YouTube video"""
        query = params.get('query', '')
        if not query:
            return {'success': False, 'message': 'No search query provided'}
        
        print(f"🎵 Opening YouTube and searching for: {query}")
        success = self.browser.search_youtube(query)
        
        if success:
            return {
                'success': True,
                'message': f'Playing "{query}" on YouTube'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to open YouTube'
            }
    
    def _search_google(self, params: dict) -> dict:
        """Search Google"""
        query = params.get('query', '')
        if not query:
            return {'success': False, 'message': 'No search query provided'}
        
        print(f"🔍 Searching Google for: {query}")
        success = self.browser.search_google(query)
        
        if success:
            return {
                'success': True,
                'message': f'Searching Google for "{query}"'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to search Google'
            }
    
    def _open_website(self, params: dict) -> dict:
        """Open a website"""
        url = params.get('url', '')
        if not url:
            return {'success': False, 'message': 'No URL provided'}
        
        # Add https:// if not present
        if not url.startswith('http'):
            url = 'https://' + url
        
        print(f"🌐 Opening website: {url}")
        success = self.browser.open_url(url)
        
        if success:
            return {
                'success': True,
                'message': f'Opening {url}'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to open website'
            }
    
    def _add_task(self, params: dict) -> dict:
        """Add a task to the to-do list"""
        title = params.get('title', '')
        description = params.get('description', '')
        
        if not title:
            return {'success': False, 'message': 'No task title provided'}
        
        task = self.task_manager.add_task(title, description)
        
        return {
            'success': True,
            'message': f'Added task: {title}',
            'task_id': task.task_id
        }
    
    def _list_tasks(self, params: dict) -> dict:
        """List tasks"""
        filter_type = params.get('filter', 'pending')  # pending, all, overdue
        
        if filter_type == 'overdue':
            tasks = self.task_manager.get_overdue_tasks()
        elif filter_type == 'all':
            tasks = self.task_manager.get_all_tasks()
        else:
            tasks = self.task_manager.get_pending_tasks()
        
        if not tasks:
            return {
                'success': True,
                'message': 'No tasks found',
                'tasks': []
            }
        
        task_list = [f"- {t.title}" + (f" (due: {t.due_time.strftime('%I:%M %p')})" if t.due_time else "") 
                     for t in tasks]
        
        return {
            'success': True,
            'message': f'You have {len(tasks)} task(s):\n' + '\n'.join(task_list),
            'tasks': [t.to_dict() for t in tasks]
        }
    
    def _complete_task(self, params: dict) -> dict:
        """Mark a task as completed"""
        task_id = params.get('task_id')
        task_title = params.get('title')
        
        if task_id:
            success = self.task_manager.complete_task(task_id)
        elif task_title:
            # Find task by title
            tasks = self.task_manager.search_tasks(task_title)
            if tasks:
                success = self.task_manager.complete_task(tasks[0].task_id)
            else:
                return {'success': False, 'message': 'Task not found'}
        else:
            return {'success': False, 'message': 'No task specified'}
        
        if success:
            return {
                'success': True,
                'message': 'Task marked as completed'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to complete task'
            }
    
    def _add_reminder(self, params: dict) -> dict:
        """Add a reminder (task with due time)"""
        title = params.get('title', '')
        minutes = params.get('minutes', 0)
        hours = params.get('hours', 0)
        
        if not title:
            return {'success': False, 'message': 'No reminder text provided'}
        
        # Calculate due time
        due_time = datetime.now() + timedelta(hours=hours, minutes=minutes)
        
        task = self.task_manager.add_task(
            title=f"Reminder: {title}",
            description="",
            due_time=due_time
        )
        
        time_str = due_time.strftime('%I:%M %p')
        return {
            'success': True,
            'message': f'Reminder set for {time_str}: {title}',
            'task_id': task.task_id
        }
    
    def parse_intent(self, user_speech: str) -> tuple:
        """
        Parse user speech to determine intent and extract parameters
        
        Returns:
            (command_type, parameters) tuple
        """
        speech_lower = user_speech.lower().strip()
        
        # Check for cancellation commands FIRST
        if any(word in speech_lower for word in ['cancel', 'never mind', 'nevermind', 'stop', 'forget it']):
            self.waiting_for_query = False
            self.last_command_type = None
            return ('cancel', {})
        
        # Ignore very short or incomplete speech (but allow single-word commands like "mute")
        if len(speech_lower) < 4 and speech_lower not in ['mute', 'lock', 'sleep']:
            return (None, {})
        
        # Check if we're waiting for a query continuation (within 10 seconds)
        current_time = time.time()
        if self.waiting_for_query and (current_time - self.last_command_time) < 10:
            # User is providing the query for the previous command
            if self.last_command_type == 'play_youtube':
                # Extract just the content (it's the query itself)
                query = user_speech.strip()
                self.waiting_for_query = False
                return ('play_youtube', {'query': query})
        
        # YouTube patterns - HIGHEST PRIORITY (most specific)
        # Must have "play" AND ("youtube" OR "music" OR "song")
        if 'play' in speech_lower and ('youtube' in speech_lower or 'music' in speech_lower or 'song' in speech_lower):
            query = self._extract_youtube_query(user_speech)
            # Check if query is incomplete (just command words, no actual content)
            if query and len(query) > 2:
                self.last_command_type = 'play_youtube'
                self.last_command_time = current_time
                self.waiting_for_query = False
                return ('play_youtube', {'query': query})
            else:
                # Incomplete query - wait for user to provide the song name
                self.last_command_type = 'play_youtube'
                self.last_command_time = current_time
                self.waiting_for_query = True
                return ('incomplete_youtube', {})
        
        # Check for "open youtube and play" without query
        if 'open' in speech_lower and 'youtube' in speech_lower and 'play' in speech_lower:
            query = self._extract_youtube_query(user_speech)
            if not query or len(query) <= 2:
                # No query provided - wait for it
                self.last_command_type = 'play_youtube'
                self.last_command_time = current_time
                self.waiting_for_query = True
                return ('incomplete_youtube', {})
            else:
                self.last_command_type = 'play_youtube'
                self.last_command_time = current_time
                self.waiting_for_query = False
                return ('play_youtube', {'query': query})
        
        # Reminder patterns - HIGH PRIORITY (before general search)
        if 'remind me' in speech_lower or 'set reminder' in speech_lower:
            title, minutes, hours = self._extract_reminder(user_speech)
            if title:
                self.waiting_for_query = False
                return ('add_reminder', {'title': title, 'minutes': minutes, 'hours': hours})
        
        # Task management patterns - HIGH PRIORITY
        if any(phrase in speech_lower for phrase in ['add task', 'create task', 'new task', 'to do']):
            title = self._extract_task_title(user_speech)
            if title:
                self.waiting_for_query = False
                return ('add_task', {'title': title})
        
        if any(phrase in speech_lower for phrase in ['list tasks', 'show tasks', 'my tasks', 'what tasks']):
            self.waiting_for_query = False
            return ('list_tasks', {'filter': 'pending'})
        
        if any(phrase in speech_lower for phrase in ['complete task', 'finish task', 'done with']):
            title = self._extract_task_title(user_speech)
            if title:
                self.waiting_for_query = False
                return ('complete_task', {'title': title})
        
        # System control patterns - HIGH PRIORITY
        # Application opening
        if any(word in speech_lower for word in ['open', 'launch', 'start', 'run']) and \
           not any(domain in speech_lower for domain in ['.com', '.org', '.net', 'website', 'youtube']):
            app_name = self._extract_app_name(user_speech)
            if app_name:
                self.waiting_for_query = False
                return ('open_application', {'app_name': app_name})
        
        # Power management
        if any(phrase in speech_lower for phrase in ['sleep', 'put to sleep', 'go to sleep']):
            self.waiting_for_query = False
            return ('sleep_computer', {})
        
        if 'shutdown' in speech_lower or 'shut down' in speech_lower or 'turn off' in speech_lower:
            self.waiting_for_query = False
            return ('shutdown_computer', {'delay': 60})
        
        if 'restart' in speech_lower or 'reboot' in speech_lower:
            self.waiting_for_query = False
            return ('restart_computer', {'delay': 60})
        
        if 'lock' in speech_lower and ('computer' in speech_lower or 'pc' in speech_lower or 'screen' in speech_lower):
            self.waiting_for_query = False
            return ('lock_computer', {})
        
        # Volume control
        if 'volume' in speech_lower:
            if 'up' in speech_lower or 'increase' in speech_lower or 'raise' in speech_lower:
                self.waiting_for_query = False
                return ('volume_up', {'increment': 10})
            elif 'down' in speech_lower or 'decrease' in speech_lower or 'lower' in speech_lower:
                self.waiting_for_query = False
                return ('volume_down', {'decrement': 10})
            elif 'set' in speech_lower or 'to' in speech_lower:
                level = self._extract_number(user_speech)
                if level is not None:
                    self.waiting_for_query = False
                    return ('set_volume', {'level': level})
        
        if 'mute' in speech_lower:
            self.waiting_for_query = False
            return ('mute', {})
        
        if 'unmute' in speech_lower:
            self.waiting_for_query = False
            return ('unmute', {})
        
        # Brightness control
        if 'brightness' in speech_lower:
            if 'up' in speech_lower or 'increase' in speech_lower or 'raise' in speech_lower:
                self.waiting_for_query = False
                return ('brightness_up', {'increment': 10})
            elif 'down' in speech_lower or 'decrease' in speech_lower or 'lower' in speech_lower:
                self.waiting_for_query = False
                return ('brightness_down', {'decrement': 10})
            elif 'set' in speech_lower or 'to' in speech_lower:
                level = self._extract_number(user_speech)
                if level is not None:
                    self.waiting_for_query = False
                    return ('set_brightness', {'level': level})
        
        # File search
        if any(phrase in speech_lower for phrase in ['search for file', 'find file', 'search file']):
            query = self._extract_search_query(user_speech)
            if query:
                self.waiting_for_query = False
                return ('search_files', {'query': query})
        
        # Window management
        if any(phrase in speech_lower for phrase in ['minimize all', 'show desktop', 'minimize windows']):
            self.waiting_for_query = False
            return ('minimize_windows', {})
        
        # Website opening patterns - MEDIUM PRIORITY
        if 'open' in speech_lower and any(domain in speech_lower for domain in ['.com', '.org', '.net', 'website']):
            url = self._extract_url(user_speech)
            if url:
                self.waiting_for_query = False
                return ('open_website', {'url': url})
        
        # Google search patterns - LOWER PRIORITY (more general, can match many things)
        # Only trigger if explicitly says "search" or "google"
        if ('search' in speech_lower and 'google' in speech_lower) or \
           ('google' in speech_lower and any(word in speech_lower for word in ['for', 'about'])) or \
           'look up' in speech_lower:
            query = self._extract_search_query(user_speech)
            # Only trigger if we have a meaningful query
            if query and len(query) > 2:
                self.waiting_for_query = False
                return ('search_google', {'query': query})
        
        return (None, {})
    
    def _extract_youtube_query(self, speech: str) -> str:
        """Extract YouTube search query from speech"""
        original = speech
        speech_lower = speech.lower()
        
        # Strategy: Find and remove the command portion, keep the rest
        
        # Pattern 1: "open youtube and play X" -> X
        if 'open youtube and play' in speech_lower:
            idx = speech_lower.find('open youtube and play')
            query = original[idx + len('open youtube and play'):].strip()
            return query
        
        # Pattern 2: "play X on youtube" -> X
        if 'on youtube' in speech_lower:
            idx = speech_lower.find('on youtube')
            before_youtube = original[:idx].strip()
            # Remove "play" from the beginning
            if before_youtube.lower().startswith('play '):
                query = before_youtube[5:].strip()
                return query
        
        # Pattern 3: "play X music/song" -> X
        if 'play' in speech_lower:
            idx = speech_lower.find('play')
            after_play = original[idx + 4:].strip()  # Skip "play"
            
            # Remove trailing "music", "song", "video"
            for suffix in [' music', ' song', ' video', ' on youtube', ' youtube']:
                if after_play.lower().endswith(suffix):
                    after_play = after_play[:-len(suffix)].strip()
            
            # Only return if we have actual content
            if after_play and len(after_play) > 0:
                return after_play
        
        # Fallback: return original minus common words
        query = original
        for word in ['open', 'youtube', 'and', 'play', 'music', 'song', 'video']:
            query = query.replace(word, ' ').replace(word.capitalize(), ' ')
        
        return ' '.join(query.split()).strip()
    
    def _extract_search_query(self, speech: str) -> str:
        """Extract search query from speech"""
        speech_lower = speech.lower()
        
        # Remove command words more carefully
        patterns_to_remove = [
            'search google for ',
            'search google ',
            'google for ',
            'google ',
            'search for ',
            'search ',
            'look up ',
            'find '
        ]
        
        for pattern in patterns_to_remove:
            if pattern in speech_lower:
                speech_lower = speech_lower.replace(pattern, '', 1)  # Only replace first occurrence
                break
        
        # Clean up extra spaces
        query = ' '.join(speech_lower.split())
        return query.strip()
    
    def _extract_url(self, speech: str) -> str:
        """Extract URL from speech"""
        # Look for domain patterns
        words = speech.lower().split()
        for word in words:
            if '.' in word and any(tld in word for tld in ['.com', '.org', '.net', '.io']):
                return word.strip('.,!?')
        
        return speech
    
    def _extract_task_title(self, speech: str) -> str:
        """Extract task title from speech"""
        speech_lower = speech.lower()
        
        # Remove command words
        for phrase in ['add task', 'create task', 'new task', 'to do', 'complete task', 'finish task', 'done with']:
            speech_lower = speech_lower.replace(phrase, '')
        
        return speech_lower.strip()
    
    def _extract_reminder(self, speech: str) -> tuple:
        """Extract reminder details from speech"""
        speech_lower = speech.lower()
        
        # Extract time
        minutes = 0
        hours = 0
        
        # Look for time patterns
        minute_match = re.search(r'(\d+)\s*minute', speech_lower)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        hour_match = re.search(r'(\d+)\s*hour', speech_lower)
        if hour_match:
            hours = int(hour_match.group(1))
        
        # Default to 5 minutes if no time specified
        if minutes == 0 and hours == 0:
            minutes = 5
        
        # Extract reminder text
        for phrase in ['remind me', 'set reminder', 'in', str(minutes), 'minute', str(hours), 'hour']:
            speech_lower = speech_lower.replace(phrase, '')
        
        title = speech_lower.strip()
        
        return (title, minutes, hours)

    
    # ==================== SYSTEM CONTROL COMMANDS ====================
    
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

    
    def _extract_app_name(self, speech: str) -> str:
        """Extract application name from speech"""
        speech_lower = speech.lower()
        
        # Remove command words
        for phrase in ['open ', 'launch ', 'start ', 'run ', 'the ', 'can you ', 'please ']:
            speech_lower = speech_lower.replace(phrase, '')
        
        # Clean up extra spaces
        speech_lower = ' '.join(speech_lower.split())
        
        # Check against known applications
        available_apps = self.system_control.get_available_applications()
        for app in available_apps:
            if app in speech_lower:
                return app
        
        # Return cleaned speech as app name
        return speech_lower.strip()
    
    def _extract_number(self, speech: str) -> Optional[int]:
        """Extract a number from speech"""
        import re
        
        # Look for numbers in the speech
        numbers = re.findall(r'\d+', speech)
        if numbers:
            return int(numbers[0])
        
        # Look for word numbers
        word_to_num = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'twenty': 20, 'thirty': 30, 'forty': 40,
            'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80,
            'ninety': 90, 'hundred': 100
        }
        
        speech_lower = speech.lower()
        for word, num in word_to_num.items():
            if word in speech_lower:
                return num
        
        return None
