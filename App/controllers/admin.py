from App.schedulers import SchedulerService, SchedulerFactory
from App.database import db
from App.controllers.user import get_user

def create_schedule(admin_id, schedule_name, strategy, staff_list, shift_length_hours, week_start):
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
        name=schedule_name,
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

    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can schedule shifts")
    if not staff or staff.role != "staff":
        raise ValueError("Invalid staff member")
    
    new_shift = admin.schedule_shift(staff_id, schedule_id, start_time, end_time)

    return new_shift


def get_shift_report(admin_id):
    admin = get_user(admin_id)
    if not admin or admin.role != "admin":
        raise PermissionError("Only admins can view shift reports")

    return admin.view_report()