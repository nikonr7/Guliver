import asyncio
from typing import Dict, Optional
from datetime import datetime, timezone
from .logging import print_step, print_success, print_error

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}

    async def add_task(self, task_id: str, user_id: str, params: dict) -> dict:
        """Add a new task to the manager."""
        task_info = {
            'id': task_id,
            'user_id': user_id,
            'status': 'pending',
            'params': params,
            'created_at': datetime.now(timezone.utc),
            'result': None,
            'error': None
        }
        self.tasks[task_id] = task_info
        return task_info

    def register_task(self, task_id: str, task: asyncio.Task):
        """Register a running task."""
        self.active_tasks[task_id] = task
        print_success(f"Task {task_id} registered")

    async def cancel_task(self, task_id: str):
        """Cancel a running task."""
        print_step(f"Attempting to cancel task {task_id}")
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            print_step(f"Found task {task_id}, cancelling...")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print_success(f"Task {task_id} cancelled successfully")
            except Exception as e:
                print_error(f"Error while cancelling task {task_id}: {str(e)}")
            finally:
                self.active_tasks.pop(task_id, None)
                if task_id in self.tasks:
                    self.tasks[task_id]['status'] = 'cancelled'
                print_success(f"Task {task_id} removed from active tasks")
        else:
            print_error(f"Task {task_id} not found in active tasks")

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get the current status of a task."""
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str, error: str = None):
        """Update the status of a task."""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = status
            if error:
                self.tasks[task_id]['error'] = error

    def clean_old_tasks(self, max_age_hours: int = 24):
        """Clean up completed tasks older than specified hours."""
        current_time = datetime.now(timezone.utc)
        to_remove = []
        
        for task_id, task_info in self.tasks.items():
            if task_info['status'] in ['completed', 'failed', 'cancelled']:
                age = current_time - task_info['created_at']
                if age.total_seconds() > max_age_hours * 3600:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            self.tasks.pop(task_id, None)
            self.active_tasks.pop(task_id, None)

# Create a global task manager instance
task_manager = TaskManager() 