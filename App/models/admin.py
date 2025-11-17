from App.database import db
from .user import User
from .shift import Shift
from .schedule import Schedule

class Admin(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "admin")
    
    def schedule_shift(self, staff_id, schedule_id, start_time, end_time):
        schedule = db.session.get(Schedule, schedule_id)
        
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
    
    def view_report(self):
        return [shift.get_json() for shift in Shift.query.order_by(Shift.start_time).all()]
