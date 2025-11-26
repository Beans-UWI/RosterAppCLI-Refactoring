from flask import Blueprint, render_template, jsonify, request, flash, send_from_directory, flash, redirect, url_for
from flask_jwt_extended import jwt_required, current_user, unset_jwt_cookies, set_access_cookies


from.index import index_views

from App.controllers import (
    login,
)
from App.controllers.user import get_user_by_username

auth_views = Blueprint('auth_views', __name__, template_folder='../templates')




'''
Page/Action Routes
'''    

@auth_views.route('/login', methods=['GET'])
def login_page():
    """Render login page"""
    return render_template('auth/login.html')

@auth_views.route('/identify', methods=['GET'])
@jwt_required()
def identify_page():
    return render_template('message.html', title="Identify", message=f"You are logged in as {current_user.id} - {current_user.username}")
    

@auth_views.route('/login', methods=['POST'])
def login_action():
    data = request.form
    token = login(data['username'], data['password'])
    
    if not token:
        flash('Bad username or password given')
        return redirect(url_for('auth_views.login_page'))
    
    # Get user to determine role for redirect
    user = get_user_by_username(data['username'])
    response = None
    
    if user:
        if user.role == 'admin':
            response = redirect('/admin')
        elif user.role == 'staff':
            response = redirect('/staff')
        else:
            response = redirect('/')
    else:
        response = redirect('/')
    
    flash('Login Successful')
    set_access_cookies(response, token) 
    return response

@auth_views.route('/logout', methods=['GET'])
def logout_action():
    response = redirect('/')
    flash("Logged Out!")
    unset_jwt_cookies(response)
    return response

'''
API Routes
'''

@auth_views.route('/api/login', methods=['POST'])
def user_login_api():
  data = request.json
  token = login(data['username'], data['password'])
  if not token:
    return jsonify(message='bad username or password given'), 401
  response = jsonify(access_token=token) 
  set_access_cookies(response, token)
  return response

@auth_views.route('/api/identify', methods=['GET'])
@jwt_required()
def identify_user():
    return jsonify({'message': f"username: {current_user.username}, id : {current_user.id}"})

@auth_views.route('/api/logout', methods=['GET'])
def logout_api():
    response = jsonify(message="Logged Out!")
    unset_jwt_cookies(response)
    return response