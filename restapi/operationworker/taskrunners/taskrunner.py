from abc import ABC, abstractmethod
from typing import Set, Tuple
from multiprocessing import Queue
from ..task import Task
from ..taskworkergroup import TaskWorkerGroup
from database.database_page import DatabasePage


class TaskRunner(ABC):
    def __init__(self, task_group: Set[TaskWorkerGroup]):
        self.task_group = task_group

    def identifier(self) -> Tuple:
        return ()

    @staticmethod
    @abstractmethod
    def unprocessed(page: DatabasePage) -> bool:
        return True

    @abstractmethod
    def run(self, task: Task, com_queue: Queue) -> dict:
        return {}
