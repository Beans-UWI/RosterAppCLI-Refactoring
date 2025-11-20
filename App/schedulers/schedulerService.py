from .scheduler import Scheduler

class SchedulerService:

    # Sets the selected scheduler
    def __init__(self, scheduler: Scheduler):
        self._scheduler = scheduler

    def generate_schedule(self, admin_id, name, staff_list, shift_length_hours, week_start):
    
        return self._scheduler.generateSchedule(
            admin_id=admin_id,
            name=name,
            staffList=staff_list,
            shift_length_hours=shift_length_hours,
            week_start=week_start,
        )
