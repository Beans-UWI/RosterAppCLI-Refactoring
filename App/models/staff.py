from App.database import db
from .user import User
from .shift import Shift
from datetime import datetime

class Staff(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "staff",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "staff")
    
    def view_roster(self):
        return [shift.get_json() for shift in Shift.query.order_by(Shift.start_time).all()]


    def clock_in(self, shift_id):
        shift = db.session.get(Shift, shift_id)

        if not shift or shift.staff_id != self.id:
            raise ValueError("Invalid shift for staff")

        if shift.clock_in is not None:
            raise ValueError("Shift is already clocked in")

        shift.clock_in = datetime.now()
        db.session.commit()
        return shift


    def clock_out(self, shift_id):
        shift = db.session.get(Shift, shift_id)

        if not shift or shift.staff_id != self.id:
            raise ValueError("Invalid shift for staff")
        
        if shift.clock_out is not None:
            raise ValueError("Shift is already clocked out")

        shift.clock_out = datetime.now()
        db.session.commit()
        return shift
