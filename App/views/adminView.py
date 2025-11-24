from flask import Blueprint, jsonify, request
from datetime import datetime
from App.controllers import admin, get_all_staff
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

admin_view = Blueprint('admin_view', __name__, template_folder='../templates')

# Admins can do the following actions:
# 1. Create Schedule, and schedule staff shifts
# 2. Get Schedule Report

@admin_view.route('/admin/create-schedule', methods=['POST'])
@jwt_required()
def createSchedule():
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        schedule_name = data.get("scheduleName") # gets the scheduleName from the request body
        strategy = data.get("strategy") # gets the strategy from the request body
        staff_list = data.get("staffList") # gets the staffList from the request body
        shift_length_hours = data.get("shiftLengthHours") # gets the shiftLengthHours from the request body
        week_start = data.get("weekStart") # gets the weekStart from the request body

        schedule = admin.create_schedule(admin_id, schedule_name, strategy, staff_list, shift_length_hours, week_start)  # Call controller method
        
        return jsonify(schedule.get_json()), 200 # Return the created schedule as JSON
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500
    

@admin_view.route('/api/admin/create-schedule', methods=['POST'])
@jwt_required()
def createSchedule_api():
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        schedule_name = data.get("scheduleName") # gets the scheduleName from the request body
        strategy = data.get("strategy") # gets the strategy from the request body
        staff_list = data.get("staffList") # gets the staffList from the request body
        shift_length_hours = data.get("shiftLengthHours") # gets the shiftLengthHours from the request body
        week_start_str = data.get("weekStart") # gets the weekStart from the request body

        raw_staff_list = data.get("staffList", [])
        staff_ids = [m.get("id") for m in raw_staff_list if m.get("id") is not None]
        staff_list = get_all_staff()
        if len(staff_list) != len(staff_ids):
            return jsonify({"error": "One or more staff IDs are invalid"}), 400

        # 2) weekStart: string -> datetime
        try:
            week_start = datetime.fromisoformat(week_start_str)
        except ValueError:
            return jsonify({"error": "weekStart must be a valid ISO datetime string"}), 400

        schedule = admin.create_schedule(admin_id, schedule_name, strategy, staff_list, shift_length_hours, week_start)  # Call controller method
        
        return jsonify(schedule.get_json()), 200 # Return the created schedule as JSON
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

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