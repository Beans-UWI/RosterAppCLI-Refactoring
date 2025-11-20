from flask import Blueprint, jsonify, request
from App.controllers import staff
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

staff_views = Blueprint('staff_views', __name__, template_folder='../templates')

# Staff can do the following actions:
# 1. View combined roster of all staff
# 2. Clock in 
# 3. Clock out
# 4. View specific shift details

@staff_views.route('/staff/roster', methods=['GET'])
@jwt_required()
def view_roster():
    try:
        staff_id = get_jwt_identity()  # get the user id stored in JWT
        roster = staff.get_combined_roster(staff_id)  # staff.get_combined_roster should return the json data of the roseter
        return jsonify(roster), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@staff_views.route('/staff/clock-in', methods=['POST'])
@jwt_required()
def clockIn():
    try:
        staff_id = int(get_jwt_identity())# db uses int for userID so we must convert
        data = request.get_json()
        shift_id = data.get("shiftId")  # gets the shiftId from the request
        shiftOBJ = staff.clock_in(staff_id, shift_id)  # Call controller
        return jsonify(shiftOBJ.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@staff_views.route('/staff/clock-out', methods=['POST'])
@jwt_required()
def clock_out():
    try:
        staff_id = int(get_jwt_identity()) # db uses int for userID so we must convert
        data = request.get_json()
        shift_id = data.get("shiftId")  # gets the shiftId from the request
        shift = staff.clock_out(staff_id, shift_id)  # Call controller
        return jsonify(shift.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500
    
@staff_views.route('/staff/shift/<shift_id>', methods=['GET'])
@jwt_required()
def view_shift(shift_id):
    try:
        shift = staff.get_shift(shift_id)  # Call controller
        if not shift:
            return jsonify({"error": "Shift not found"}), 404
        return jsonify(shift.get_json()), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500