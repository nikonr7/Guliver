import asyncio
from typing import Dict
from .logging import print_step, print_success, print_error

# Store active search tasks
active_tasks: Dict[str, asyncio.Task] = {}

async def cancel_task(task_id: str):
    """Cancel a running task by its ID."""
    print_step(f"Attempting to cancel task {task_id}")
    if task_id in active_tasks:
        task = active_tasks[task_id]
        print_step(f"Found task {task_id}, cancelling...")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print_success(f"Task {task_id} cancelled successfully")
        except Exception as e:
            print_error(f"Error while cancelling task {task_id}: {str(e)}")
        finally:
            active_tasks.pop(task_id, None)
            print_success(f"Task {task_id} removed from active tasks")
    else:
        print_error(f"Task {task_id} not found in active tasks")

def register_task(task_id: str, task: asyncio.Task):
    """Register a new task in the task manager."""
    active_tasks[task_id] = task
    print_success(f"Task {task_id} registered")

def remove_task(task_id: str):
    """Remove a task from the task manager."""
    if task_id in active_tasks:
        active_tasks.pop(task_id)
        print_success(f"Task {task_id} removed")
    else:
        print_error(f"Task {task_id} not found")

def get_task(task_id: str) -> asyncio.Task:
    """Get a task by its ID."""
    return active_tasks.get(task_id) 