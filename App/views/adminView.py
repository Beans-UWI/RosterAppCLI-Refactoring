from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for, current_app
from datetime import datetime, timedelta
from App.controllers import admin, get_all_staff
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
    report_type = request.args.get('reportType', '').lower()
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    report = admin.get_shift_report(admin_id)
    report_data = report if isinstance(report, list) else []

    start_date = end_date = None

    def parse_date(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    if start_date_str:
        start_date = parse_date(start_date_str)
        if not start_date:
            flash('Invalid start date. Please use YYYY-MM-DD format.', 'error')
            return redirect(url_for('admin_view.admin_shift_report'))

    if end_date_str:
        end_date = parse_date(end_date_str)
        if not end_date:
            flash('Invalid end date. Please use YYYY-MM-DD format.', 'error')
            return redirect(url_for('admin_view.admin_shift_report'))

    if report_type not in {'daily', 'weekly', 'monthly'}:
        report_type = ''

    if not start_date and not end_date and report_type:
        today = datetime.utcnow().date()
        if report_type == 'daily':
            start_date = end_date = today
        elif report_type == 'weekly':
            start_date = today - timedelta(days=6)
            end_date = today
        elif report_type == 'monthly':
            start_date = today - timedelta(days=29)
            end_date = today

    if start_date and not end_date:
        end_date = start_date
    if end_date and not start_date:
        start_date = end_date
    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date

    if start_date and end_date:
        filtered_report = []
        for shift in report_data:
            shift_date_str = shift.get("start_date")
            if not shift_date_str:
                continue
            try:
                shift_date = datetime.strptime(shift_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if start_date <= shift_date <= end_date:
                filtered_report.append(shift)
    else:
        filtered_report = report_data

    selected_start = start_date.isoformat() if start_date else ''
    selected_end = end_date.isoformat() if end_date else ''

    return render_template(
        'admin/index.html',
        report_data=filtered_report,
        selected_report_type=report_type,
        selected_start_date=selected_start,
        selected_end_date=selected_end,
    )

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
    password = data.get('password')
    confirm_password = data.get('confirmPassword')

    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect('/admin/create-account')

    new_user = create_user(
        data['username'],
        password,
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
    is_json = request.is_json

    def respond_error(message, status_code=400):
        if is_json:
            return jsonify({"error": message}), status_code
        flash(message, 'error')
        return redirect(url_for('admin_view.admin_create_schedule'))

    try:
        admin_id = get_jwt_identity()
        data = request.get_json() if is_json else request.form

        schedule_name = data.get("scheduleName")
        strategy = data.get("strategy")
        shift_length_hours = data.get("shiftLengthHours")
        week_start_str = data.get("weekStart")

        if not schedule_name or not strategy or not shift_length_hours or not week_start_str:
            return respond_error("All fields are required.")

        try:
            shift_length_hours = int(shift_length_hours)
        except (TypeError, ValueError):
            return respond_error("shiftLengthHours must be a number.")

        # Collect staff IDs from either JSON or form submissions
        if is_json:
            raw_staff_list = data.get("staffList", [])
            if raw_staff_list and isinstance(raw_staff_list[0], dict):
                staff_ids = [
                    member.get("id") for member in raw_staff_list if member.get("id") is not None
                ]
            else:
                staff_ids = raw_staff_list
        else:
            staff_ids = data.getlist("staffList")

        if not staff_ids:
            return respond_error("staffList cannot be empty.")

        try:
            staff_ids = [int(staff_id) for staff_id in staff_ids]
        except (TypeError, ValueError):
            return respond_error("Staff IDs must be integers.")

        staff_list = [db.session.get(Staff, staff_id) for staff_id in staff_ids]
        if None in staff_list:
            return respond_error("One or more staff IDs are invalid.")

        # Convert weekStart string to datetime
        try:
            week_start = datetime.fromisoformat(week_start_str)
        except ValueError:
            return respond_error("weekStart must be a valid ISO date (YYYY-MM-DD).")

        schedule = admin.create_schedule(
            admin_id, schedule_name, strategy, staff_list, shift_length_hours, week_start
        )

        if is_json:
            return jsonify(schedule.get_json()), 200

        flash('Schedule created successfully!', 'success')
        return redirect(url_for('admin_view.admin_create_schedule'))
    except (PermissionError, ValueError) as e:
        if is_json:
            return jsonify({"error": str(e)}), 403
        flash(str(e), 'error')
        return redirect(url_for('admin_view.admin_create_schedule'))
    except SQLAlchemyError:
        if is_json:
            return jsonify({"error": "Database error"}), 500
        flash('Database error', 'error')
        return redirect(url_for('admin_view.admin_create_schedule'))
    

@admin_view.route('/api/admin/create-schedule', methods=['POST'])
@jwt_required()
def createSchedule_api():
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        schedule_name = data.get("scheduleName") # gets the scheduleName from the request body
        strategy = data.get("strategy") # gets the strategy from the request body
        shift_length_hours = data.get("shiftLengthHours") # gets the shiftLengthHours from the request body
        week_start_str = data.get("weekStart") # gets the weekStart from the request body

        # Extract staff IDs from the request
        raw_staff_list = data.get("staffList", [])
        staff_ids = [m.get("id") for m in raw_staff_list if m.get("id") is not None]
        
        if not staff_ids:
            return jsonify({"error": "staffList cannot be empty"}), 400

        # Convert staff IDs to Staff objects (only selected staff, not all staff)
        staff_list = [db.session.get(Staff, staff_id) for staff_id in staff_ids]
        # Validate that all staff IDs are valid
        if None in staff_list:
            return jsonify({"error": "One or more staff IDs are invalid"}), 400

        # Convert weekStart string to datetime
        try:
            week_start = datetime.fromisoformat(week_start_str)
        except ValueError:
            return jsonify({"error": "weekStart must be a valid ISO datetime string"}), 400

        schedule = admin.create_schedule(admin_id, schedule_name, strategy, staff_list, shift_length_hours, week_start)  # Call controller method
        
        return jsonify(schedule.get_json()), 200 # Return the created schedule as JSON
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        current_app.logger.exception("Database error while creating schedule via API")
        return jsonify({"error": "Database error"}), 500
    except Exception:
        current_app.logger.exception("Unexpected error while creating schedule via API")
        return jsonify({"error": "Unexpected error"}), 500

@admin_view.route('/admin/create-shift', methods=['POST'])
@jwt_required()
def createShift():
    is_json = request.is_json

    def respond_error(message, status_code=400):
        if is_json:
            return jsonify({"error": message}), status_code
        flash(message, 'error')
        return redirect(url_for('admin_view.admin_schedule_shift'))

    try:
        admin_id = get_jwt_identity()
        data = request.get_json() if is_json else request.form

        staff_id = data.get("staffId")
        schedule_id = data.get("scheduleId")

        if not staff_id or not schedule_id:
            return respond_error("staffId and scheduleId are required.")

        try:
            staff_id = int(staff_id)
            schedule_id = int(schedule_id)
        except (TypeError, ValueError):
            return respond_error("IDs must be integers.")

        if is_json:
            start_time_str = data.get("startTime")
            end_time_str = data.get("endTime")
        else:
            date_str = data.get("date")
            start_time_part = data.get("startTime")
            end_time_part = data.get("endTime")
            if not date_str or not start_time_part or not end_time_part:
                return respond_error("Date, start time, and end time are required.")
            start_time_str = f"{date_str} {start_time_part}:00"
            end_time_str = f"{date_str} {end_time_part}:00"

        if not start_time_str or not end_time_str:
            return respond_error("Start and end times are required.")

        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            try:
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return respond_error("Invalid date format. Use ISO or YYYY-MM-DD HH:MM:SS.")

        shift = admin.schedule_shift(admin_id, staff_id, schedule_id, start_time, end_time)

        if is_json:
            return jsonify(shift.get_json()), 200

        flash('Shift created successfully!', 'success')
        return redirect(url_for('admin_view.admin_schedule_shift'))
    except (PermissionError, ValueError) as e:
        if is_json:
            return jsonify({"error": str(e)}), 403
        flash(str(e), 'error')
        return redirect(url_for('admin_view.admin_schedule_shift'))
    except SQLAlchemyError:
        if is_json:
            return jsonify({"error": "Database error"}), 500
        flash('Database error', 'error')
        return redirect(url_for('admin_view.admin_schedule_shift'))

@admin_view.route('/api/admin/shift-report', methods=['GET'])
@jwt_required()
def shiftReport_api():
    try:
        admin_id = get_jwt_identity()
        report = admin.get_shift_report(admin_id)  # Call controller method
        return jsonify(report), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500