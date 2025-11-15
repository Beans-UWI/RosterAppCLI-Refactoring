from App.database import db
from abc import ABC, abstractmethod

class Scheduler(ABC):
    @abstractmethod
    def generateSchedule(self, admin_id, name, staffList, shift_length_hours, week_start):
        pass