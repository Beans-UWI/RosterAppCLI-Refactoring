from App.models import Shift
from App.database import db
from App.controllers.user import get_user

def get_combined_roster(staff_id):
    staff = get_user(staff_id)
    if not staff or staff.role != "staff":
        raise PermissionError("Only staff can view roster")
    return staff.view_roster()


def clock_in(staff_id, shift_id):
    staff = get_user(staff_id)
    if not staff or staff.role != "staff":
        raise PermissionError("Only staff can clock in")

    shift = staff.clock_in(shift_id)
    return shift


def clock_out(staff_id, shift_id):
    staff = get_user(staff_id)
    if not staff or staff.role != "staff":
        raise PermissionError("Only staff can clock out")

    shift = staff.clock_out(shift_id)
    return shift

def get_shift(shift_id):
    shift = db.session.get(Shift, shift_id)
    return shift