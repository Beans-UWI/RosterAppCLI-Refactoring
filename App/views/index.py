from flask import Blueprint, redirect, render_template, request, send_from_directory, jsonify
from App.controllers import create_user, initialize
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from App.models import User

index_views = Blueprint('index_views', __name__, template_folder='../templates')

@index_views.route('/', methods=['GET'])
def index_page():
    """Main landing page - redirects authenticated users to their dashboard"""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        
        if identity:
            user = User.query.get(identity)
            if user:
                # Redirect based on role
                if user.role == 'admin':
                    return redirect('/admin')
                elif user.role == 'staff':
                    return redirect('/staff')
    except Exception as e:
        # Not authenticated or error - show landing page
        pass
    
    return render_template('index.html')

@index_views.route('/init', methods=['GET'])
def init():
    initialize()
    return jsonify(message='db initialized!')

@index_views.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status':'healthy'})