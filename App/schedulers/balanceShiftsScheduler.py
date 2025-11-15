from App.database import db
from .scheduler import Scheduler

class BalanceShiftsScheduler(Scheduler):
    def generateSchedule(self, admin_id, name, staffList, shift_length_hours, week_start):
        return