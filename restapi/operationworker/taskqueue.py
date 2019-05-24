from typing import List, Optional, Set, TYPE_CHECKING
from .task import Task, \
    TaskAlreadyQueuedException, TaskNotFinishedException, TaskNotFoundException, \
    TaskStatusCodes, TaskStatus
from .taskrunners.taskrunner import TaskRunner
from multiprocessing import Lock
import time
from .taskworkergroup import TaskWorkerGroup


class TaskQueue:
    def __init__(self):
        self.tasks: List[Task] = []
        self.mutex = Lock()

    def remove(self, task_id: str) -> Optional[Task]:
        with self.mutex:
            for i, t in enumerate(self.tasks):
                if t.task_id == task_id:
                    del self.tasks[i]
                    return t

            return None

    def put(self, task_id: str, task_data):
        with self.mutex:
            for task in self.tasks:
                if task.task_id == task_id:
                    raise TaskAlreadyQueuedException(task_id)

            self.tasks.append(Task(task_id, task_data, TaskStatus(code=TaskStatusCodes.QUEUED), {}))

    def pop_result(self, task_id: str) -> dict:
        with self.mutex:
            for i, t in enumerate(self.tasks):
                if t.task_id == task_id:
                    if t.task_status.code == TaskStatusCodes.QUEUED or t.task_status.code == TaskStatusCodes.RUNNING:
                        raise TaskNotFinishedException()

                    del self.tasks[i]
                    return t.task_result

            raise TaskNotFoundException()

    def status(self, task_id: str) -> TaskStatus:
        with self.mutex:
            for task in self.tasks:
                if task.task_id == task_id:
                    return task.task_status

            return TaskStatus(TaskStatusCodes.NOT_FOUND)

    def update_status(self, task_id: str, status: TaskStatus):
        with self.mutex:
            for task in self.tasks:
                if task.task_id == task_id:
                    task.task_status = status
                    return

            raise TaskNotFoundException()

    def next_unprocessed(self, groups: Set[TaskWorkerGroup], sleep_secs=1.0) -> Task:
        while True:
            with self.mutex:
                for task in self.tasks:
                    if not any([g in groups for g in task.task_runner.task_group]):
                        # not in set
                        continue

                    if task.task_status.code == TaskStatusCodes.QUEUED:
                        task.task_status.code = TaskStatusCodes.RUNNING
                        return task

            time.sleep(sleep_secs)

    def id_by_runner(self, task_runner: TaskRunner) -> Optional[str]:
        with self.mutex:
            for task in self.tasks:
                if task.task_runner == task_runner or (type(task.task_runner) == type(task_runner) and task.task_runner.identifier() == task_runner.identifier()):
                    return task.task_id
        return None

    def task_finished(self, task: Task, result):
        with self.mutex:
            task.task_status.code = TaskStatusCodes.FINISHED
            task.task_result = result

    def task_error(self, task: Task, result):
        with self.mutex:
            task.task_status.code = TaskStatusCodes.ERROR
            task.task_result = result
