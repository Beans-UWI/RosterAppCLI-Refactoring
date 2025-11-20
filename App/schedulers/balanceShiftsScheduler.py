from App.database import db
from .scheduler import Scheduler
from App.models import Schedule, Shift
from datetime import datetime, timedelta


class BalanceShiftsScheduler(Scheduler):
    def generateSchedule(self, admin_id, name, staffList, shift_length_hours, week_start):
        if not staffList:
            raise ValueError("Staff list cannot be empty")
        if 24 % shift_length_hours != 0:
            raise ValueError("Shift length must divide 24 evenly (e.g., 6, 8, 12 hours)")
        
        shifts_per_day = 24 // shift_length_hours
        total_days = 7
        total_shifts = shifts_per_day * total_days
        staff_count = len(staffList)

        new_schedule = Schedule(
            created_by=admin_id,
            name=name,
            created_at=datetime.utcnow(),
            start_date=week_start
        )
        db.session.add(new_schedule)
        db.session.flush()

        def is_day_shift(start_time):
            """
            Day shifts: 06:00 - 18:00 (6 AM to 6 PM)
            Night shifts: 18:00 - 06:00 (6 PM to 6 AM)
            """
            hour = start_time.hour
            return 6 <= hour < 18
        

        # Generate all shifts with their times first
        shift_info = []
        for shift_idx in range(total_shifts):
            day_offset = shift_idx // shifts_per_day
            block_idx = shift_idx % shifts_per_day

            start_time = week_start + timedelta(days=day_offset, hours=block_idx * shift_length_hours)
            end_time = start_time + timedelta(hours=shift_length_hours)
            
            shift_info.append({
                'start_time': start_time,
                'end_time': end_time,
                'is_day': is_day_shift(start_time)
            })

        # Track day/night shift counts per staff member
        staff_day_counts = [0] * staff_count
        staff_night_counts = [0] * staff_count

        new_shifts = []

        """
        Balanced Day/Night Shift Assignment
        Strategy:
        1. Sort shifts to separate day and night shifts
        2. For each shift, assign to staff member with:
           - Fewer shifts of that type (day or night)
           - If tied, use round-robin within that group
        
        This ensures:
        - Each staff gets balanced day/night shifts
        - Difference in day shifts between any two staff <= 1
        - Difference in night shifts between any two staff <= 1
        """

        for shift_idx, shift in enumerate(shift_info):
            if shift['is_day']:
                min_day_count = min(staff_day_counts)
                candidates = [i for i in range(staff_count) if staff_day_counts[i] == min_day_count]
                
                if len(candidates) > 1:
                    total_counts = [staff_day_counts[i] + staff_night_counts[i] for i in candidates]
                    min_total = min(total_counts)
                    candidates = [i for i in candidates if staff_day_counts[i] + staff_night_counts[i] == min_total]
                
                selected_staff_idx = candidates[shift_idx % len(candidates)]
                staff_day_counts[selected_staff_idx] += 1
            else:
                min_night_count = min(staff_night_counts)
                candidates = [i for i in range(staff_count) if staff_night_counts[i] == min_night_count]
                
                if len(candidates) > 1:
                    total_counts = [staff_day_counts[i] + staff_night_counts[i] for i in candidates]
                    min_total = min(total_counts)
                    candidates = [i for i in candidates if staff_day_counts[i] + staff_night_counts[i] == min_total]
                
                selected_staff_idx = candidates[shift_idx % len(candidates)]
                staff_night_counts[selected_staff_idx] += 1

            staff = staffList[selected_staff_idx]

            new_shifts.append(
                Shift(
                    staff_id=staff.id,
                    schedule_id=new_schedule.id,
                    start_time=shift['start_time'],
                    end_time=shift['end_time']
                )
            )

        db.session.add_all(new_shifts)
        db.session.commit()

        return new_schedule