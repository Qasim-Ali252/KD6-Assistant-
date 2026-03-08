"""
Task Manager Module
Manages reminders, to-do lists, and scheduled tasks
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os

class Task:
    """Represents a task or reminder"""
    def __init__(self, task_id: str, title: str, description: str = "", 
                 due_time: Optional[datetime] = None, completed: bool = False):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.due_time = due_time
        self.completed = completed
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'due_time': self.due_time.isoformat() if self.due_time else None,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data):
        task = Task(
            task_id=data['task_id'],
            title=data['title'],
            description=data.get('description', ''),
            due_time=datetime.fromisoformat(data['due_time']) if data.get('due_time') else None,
            completed=data.get('completed', False)
        )
        if 'created_at' in data:
            task.created_at = datetime.fromisoformat(data['created_at'])
        return task

class TaskManager:
    """Manages tasks and reminders"""
    
    def __init__(self, config):
        self.config = config
        self.tasks_file = 'memory/tasks.json'
        self.tasks: List[Task] = []
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from disk"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
            except Exception as e:
                print(f"Error loading tasks: {e}")
                self.tasks = []
    
    def _save_tasks(self):
        """Save tasks to disk"""
        os.makedirs('memory', exist_ok=True)
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'tasks': [t.to_dict() for t in self.tasks]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def add_task(self, title: str, description: str = "", due_time: Optional[datetime] = None) -> Task:
        """Add a new task"""
        task_id = f"task_{len(self.tasks)}_{int(datetime.now().timestamp())}"
        task = Task(task_id, title, description, due_time)
        self.tasks.append(task)
        self._save_tasks()
        return task
    
    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed"""
        for task in self.tasks:
            if task.task_id == task_id:
                task.completed = True
                self._save_tasks()
                return True
        return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                self.tasks.pop(i)
                self._save_tasks()
                return True
        return False
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending (not completed) tasks"""
        return [t for t in self.tasks if not t.completed]
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get tasks that are overdue"""
        now = datetime.now()
        return [t for t in self.tasks 
                if not t.completed and t.due_time and t.due_time < now]
    
    def get_upcoming_tasks(self, hours: int = 24) -> List[Task]:
        """Get tasks due in the next N hours"""
        now = datetime.now()
        future = now + timedelta(hours=hours)
        return [t for t in self.tasks 
                if not t.completed and t.due_time and now < t.due_time < future]
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return self.tasks
    
    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title or description"""
        query_lower = query.lower()
        return [t for t in self.tasks 
                if query_lower in t.title.lower() or query_lower in t.description.lower()]
