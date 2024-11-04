from flask import Blueprint, request, jsonify
from config import *
from data_classes import User
from flask_jwt_extended import create_access_token
from datetime import datetime
from tinydb import Query
import pytz

auth = Blueprint('auth', __name__, url_prefix="/login")

@auth.route('/code', methods=['POST'])
def code():
    # Get email from the frontend
    email = request.json.get('email', 'demo@example.com')
    
    # Mock user info (similar to what Google would provide)
    given_name = email.split('@')[0].capitalize()
    family_name = 'User'
    picture = f'https://api.dicebear.com/7.x/avataaars/svg?seed={email}'

    # Query TinyDB
    User_Query = Query()
    user_data = user_table.get(User_Query.email == email)

    user_create_topic_permission = True

    # Time 
    pst = pytz.timezone('America/Los_Angeles')
    current_time_pst = datetime.now(pst).strftime('%Y-%m-%d %H:%M:%S')

    if not user_data:
        # Create a new user if not already existing
        user_data = {
            'userId': email,
            'email': email,
            'given_name': given_name,
            'nickname': given_name, 
            'family_name': family_name,
            'photo': picture, 
            'secrets_revealed': None,
            'conversations': [],
            'created_topics': [],
            'active_checkout_session': {
                'session_id': None,
                'timestamp': None
            },
            'subscribed': {
                'state': False,
                'id': None,
                'stripe_id': None
            },
            'screen_mode': 1,
            'timestamp': current_time_pst,
        }
        isSubscribed = False
        user_table.insert(user_data)
        user = User(user_data)
    else:
        # User already exists in the database
        update_required = False
        
        # Check if given_name, family_name, or photo are missing and update if required
        if not user_data.get('given_name'):
            user_data['given_name'] = given_name
            user_data['nickname'] = given_name
            update_required = True
        if not user_data.get('family_name'):
            user_data['family_name'] = family_name
            update_required = True
        if not user_data.get('photo'):
            user_data['photo'] = picture
            update_required = True
        
        if update_required:
            user_table.update(user_data, User_Query.email == email)

        isSubscribed = user_data.get('subscribed', {}).get('state', False)

        if not isSubscribed:
            if len(user_data.get('created_topics', [])) >= max_topic_topics_WO_sub:
                user_create_topic_permission = False

        user = User(user_data)

    # Generate JWT token
    access_token = ""

    result = {
        "access_token": access_token,
        'given_name': given_name,
        'family_name': family_name,
        'photo': picture,
        'user_create_topic_permission': user_create_topic_permission,
        'isSubscribed': isSubscribed
    }
    
    return jsonify(result), 200