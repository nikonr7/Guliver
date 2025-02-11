import asyncio
from .log_utils import *

async def cancel_task(task_id: str, active_tasks):
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