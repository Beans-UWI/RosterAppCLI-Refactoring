from datetime import datetime, timedelta, timezone
from App.database import db
from .scheduler import Scheduler
from App.models import Shift
from App.models import Schedule

class MinimizeDaysScheduler(Scheduler):
    def generateSchedule(self, admin_id, name, staffList, shift_length_hours, week_start):
        
        if not staffList:
            raise ValueError("staffList cannot be empty.")

        if 24 % shift_length_hours != 0:
            raise ValueError("shift_length_hours must evenly divide 24 (e.g., 12, 8, 6, 4).")

        
        if week_start is None:
            now = datetime.now(timezone.utc)
            week_start = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)

        total_days = 7
        shifts_per_day = 24 // shift_length_hours
        staff_count = len(staffList)

        new_schedule = Schedule(
            created_by=admin_id,
            name=name,
            created_at=datetime.now(timezone.utc),
            start_date = week_start
        )
        db.session.add(new_schedule)
        db.session.flush()

        new_shifts = []
        """
        Each person will work an entire day to minimize the days they work

        """
        for day_idx in range(total_days):
            staff = staffList[day_idx % staff_count]  # one person per day, rotating
            day_start = week_start + timedelta(days=day_idx)

            for block_idx in range(shifts_per_day):
                start_time = day_start + timedelta(hours=block_idx * shift_length_hours)
                end_time = start_time + timedelta(hours=shift_length_hours)

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
