from App.models import Shift
from App.schedulers import SchedulerService, SchedulerFactory
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

from App.models import Shift, Schedule
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

def create_schedule(admin_id, scheduleName, strategy, staff_list, shift_length_hours, week_start):
    admin = get_user(admin_id)
    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can create schedules")

    # Get the selected scheduling strategy class
    scheduler = SchedulerFactory.get_scheduler(strategy)

    # Get the selected scheduling strategy's implementation
    service = SchedulerService(scheduler)

    # Apply the selected scheduling strategy's implementation to generate a new schedule
    new_schedule = service.generate_schedule(
        admin_id=admin_id,
        name=scheduleName,
        staff_list=staff_list,
        shift_length_hours=shift_length_hours,
        week_start=week_start,
    )

    db.session.add(new_schedule)
    db.session.commit()

    return new_schedule

def schedule_shift(admin_id, staff_id, schedule_id, start_time, end_time):
    admin = get_user(admin_id)
    staff = get_user(staff_id)

    schedule = db.session.get(Schedule, schedule_id)

    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can schedule shifts")
    if not staff or staff.role != "staff":
        raise ValueError("Invalid staff member")
    if not schedule:
        raise ValueError("Invalid schedule ID")

    new_shift = Shift(
        staff_id=staff_id,
        schedule_id=schedule_id,
        start_time=start_time,
        end_time=end_time
    )

    db.session.add(new_shift)
    db.session.commit()

    return new_shift


def get_shift_report(admin_id):
    admin = get_user(admin_id)
    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can view shift reports")

    return [shift.get_json() for shift in Shift.query.order_by(Shift.start_time).all()]