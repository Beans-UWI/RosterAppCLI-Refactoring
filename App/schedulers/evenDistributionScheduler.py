from App.database import db
from .scheduler import Scheduler
from App.models import Shift
from App.models import Schedule
from datetime import datetime, timedelta

class EvenDistributionScheduler(Scheduler):
    def generateSchedule(self, admin_id, name, staffList, shift_length_hours, week_start):
        if not staffList:
            raise ValueError("staffList cannot be empty.")

        if 24 % shift_length_hours != 0:
            raise ValueError("shift_length_hours must divide 24 evenly (e.g., 12, 8, 6, 4).")
        
        shifts_per_day = 24 // shift_length_hours
        total_days = 7
        total_shifts = total_days * shifts_per_day
        staff_count = len(staffList)

        new_schedule = Schedule(
            created_by=admin_id,
            name=name,
            created_at=datetime.utcnow(),
            start_date=week_start
        )
        db.session.add(new_schedule)
        db.session.flush()

        new_shifts = []

        """
        Round Robin Approach
        Eg. If staff_count = 3, total_shifts = 24
                Staff 1 will work Shift 1
                Staff 2 will work Shift 2
                Staff 3 will work Shift 3

                Staff 1 will work Shift 4
                Staff 2 will work Shift 5
                Staff 3 will work Shift 6
                .
                .
                .

        """
        for shift_idx in range(total_shifts):
            day_offset = shift_idx // shifts_per_day
            block_idx = shift_idx % shifts_per_day

            start_time = week_start + timedelta(days=day_offset, hours=block_idx * shift_length_hours)
            end_time = start_time + timedelta(hours=shift_length_hours)

            staff = staffList[shift_idx % staff_count]

            new_shifts.append(
                Shift(
                    staff_id=staff.id,
                    schedule_id=new_schedule.id,
                    start_time=start_time,
                    end_time=end_time
                )
            )

        db.session.add_all(new_shifts)
        db.session.commit()

        return new_schedule