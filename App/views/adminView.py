from flask import Blueprint, jsonify, request, render_template, flash, redirect
from datetime import datetime
from App.controllers import admin
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from App.models import Shift, User, Staff, Schedule
from App.database import db

admin_view = Blueprint('admin_view', __name__, template_folder='../templates')

# Admins can do the following actions:
# 1. Create Schedule, and schedule staff shifts
# 2. Get Schedule Report


@admin_view.route('/admin', methods=['GET'])
@admin_view.route('/admin/schedule', methods=['GET'])
@jwt_required()
def admin_schedule():
    shifts = [shift.get_json() for shift in Shift.query.order_by(Shift.start_time).all()]
    return render_template('admin/index.html', shifts=shifts)

# Page route - renders template with users data
@admin_view.route('/admin/users', methods=['GET'])
@jwt_required()
def admin_users():
    users = User.query.all()
    return render_template('admin/index.html', users=users)

# Page route - renders template with staff and schedules data
@admin_view.route('/admin/schedule-shift', methods=['GET'])
@jwt_required()
def admin_schedule_shift():
    staff_list = Staff.query.all()
    schedules = Schedule.query.all()
    return render_template('admin/index.html', staff_list=staff_list, schedules=schedules)

@admin_view.route('/admin/create-schedule', methods=['GET'])
@jwt_required()
def admin_create_schedule():
    staff_list = Staff.query.all()
    return render_template('admin/index.html', staff_list=staff_list)

# Page route - renders template with report data
@admin_view.route('/admin/shift-report', methods=['GET'])
@jwt_required()
def admin_shift_report():
    admin_id = get_jwt_identity()
    report = admin.get_shift_report(admin_id)
    report_data = report if isinstance(report, list) else []
    return render_template('admin/index.html', report_data=report_data)

# Page route - renders template
@admin_view.route('/admin/create-account', methods=['GET'])
@jwt_required()
def admin_create_account():
    return render_template('admin/index.html')

# Form handling route - redirects back to page
@admin_view.route('/admin/create-account', methods=['POST'])
@jwt_required()
def create_account_action():
    from App.controllers import create_user
    data = request.form
    new_user = create_user(
        data['username'],
        data['password'],
        data['role']
    )
    if new_user:
        flash('Account created successfully!', 'success')
    else:
        flash('Failed to create account', 'error')
    return redirect('/admin/create-account')
    
@admin_view.route('/admin/create-schedule', methods=['POST'])
@jwt_required()
def createSchedule():
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        schedule_name = data.get("scheduleName") # gets the scheduleName from the request body
        strategy = data.get("strategy") # gets the strategy from the request body
        staff_list_ids = data.get("staffList") # gets the staffList from the request body (list of IDs)
        shift_length_hours = data.get("shiftLengthHours") # gets the shiftLengthHours from the request body
        week_start_str = data.get("weekStart") # gets the weekStart from the request body (string)
        
        # Parse week_start from string to datetime
        if week_start_str:
            try:
                # Parse date string (format: "YYYY-MM-DD")
                from datetime import timezone
                week_start = datetime.strptime(week_start_str, "%Y-%m-%d")
                # Set to UTC timezone and set time to midnight
                week_start = week_start.replace(tzinfo=timezone.utc)
            except ValueError as e:
                return jsonify({"error": f"Invalid date format: {week_start_str}. Expected YYYY-MM-DD"}), 400
        else:
            week_start = None
        
        # Convert staff IDs to Staff objects
        staff_list = []
        if staff_list_ids:
            for staff_id in staff_list_ids:
                staff = db.session.get(Staff, staff_id)
                if staff:
                    staff_list.append(staff)
                else:
                    return jsonify({"error": f"Invalid staff ID: {staff_id}"}), 400
        
        schedule = admin.create_schedule(admin_id, schedule_name, strategy, staff_list, shift_length_hours, week_start)  # Call controller method
        
        return jsonify(schedule.get_json()), 200 # Return the created schedule as JSON
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError as e:
        # Log the actual database error for debugging
        import traceback
        print(f"Database error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        # Catch any other unexpected errors
        import traceback
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Error: {str(e)}"}), 500

@admin_view.route('/admin/create-shift', methods=['POST'])
@jwt_required()
def createShift():
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        schedule_id = data.get("scheduleId") # gets the scheduleId from the request body
        staff_id = data.get("staffId") # gets the staffId from the request body
        start_time_str = data.get("startTime") # gets the startTime from the request body
        end_time_str = data.get("endTime") # gets the endTime from the request body

    # Try ISO first, fallback to "YYYY-MM-DD HH:MM:SS"
        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

        shift = admin.schedule_shift(admin_id, staff_id, schedule_id, start_time, end_time)  # Call controller method
        print("Debug: Created shift in view:", shift.get_json())
        
        return jsonify(shift.get_json()), 200 # Return the created shift as JSON
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@admin_view.route('/admin/shift-report', methods=['GET'])
@jwt_required()
def shiftReport():
    try:
        admin_id = get_jwt_identity()
        report = admin.get_shift_report(admin_id)  # Call controller method
        return jsonify(report), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500