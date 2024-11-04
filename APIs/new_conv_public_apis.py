from flask import Flask, redirect, url_for, request, jsonify, stream_with_context, Blueprint
from flask_dance.contrib.google import make_google_blueprint, google
from tutor_agent.Conv_handler_improved_mem import TeachingAssistant_stream
from flask_login import UserMixin, LoginManager, logout_user, login_user, login_required, current_user
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask import render_template, make_response, stream_with_context, Response
from init_agent.Conv_Creator_basics import ConvCreator_stream
import config
from text_to_speech.TTS import TTS_blueprint
import random
import uuid 
import logging
from tinydb import Query
from datetime import datetime
import pytz
import sys

public_blueprint = Blueprint('public', __name__)

logger = logging.getLogger(__name__)


@public_blueprint.route('/api/v1/create_conv_id_public', methods=['POST'])
def Create_conv_id_public():
    new_id = str(uuid.uuid4())
    response = {
       'id': new_id
    }
    return jsonify(response), 200

@public_blueprint.route('/api/v1/Conv_first_massage_public', methods=['POST'])
def Conv_first_massage_public():
    try:
        current_user_email = 'user@public.com'
        data = request.get_json()
        conv_id = data['id']
        
        # TinyDB query
        User_Query = Query()
        user = config.user_table.get(User_Query.email == current_user_email)
        
        if not user:
            logger.info(f"Creating new public user: {current_user_email}")
            # Mock user info
            given_name = current_user_email.split('@')[0].capitalize()
            family_name = 'User'
            picture = f'https://api.dicebear.com/7.x/avataaars/svg?seed={current_user_email}'

            # Time 
            pst = pytz.timezone('America/Los_Angeles')
            current_time_pst = datetime.now(pst).strftime('%Y-%m-%d %H:%M:%S')

            # Create new user data
            user = {
                'userId': current_user_email,
                'email': current_user_email,
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
            config.user_table.insert(user)
            logger.info(f"Created new public user: {user}")
            
        CC = ConvCreator_stream(
            api_keys=config.API_KEYS,
            conversation_model=config.conversation_model, 
            extraction_model=config.extraction_model, 
            temperature=0, 
            conv_id=conv_id,
        )
        
        return Response(CC.handle_first_message(user), mimetype='text/event-stream')
        
    except Exception as e:
        logger.error(f"Error in Conv_first_massage_public: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@public_blueprint.route('/api/v1/Conv_next_massage_public', methods=['POST'])
def Conv_next_massage_public():
    current_user_email = 'user@public.com'
    response = config.user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    data = request.get_json()
    user_input = data['user_input']
    conv_id = data['id']
    CC = ConvCreator_stream(
        api_keys=config.API_KEYS, 
        conversation_model = config.conversation_model, 
        extraction_model = config.extraction_model, 
        temperature=0,
        conv_id = conv_id,
        )
    return Response(CC.handle_message(user_input, user), mimetype='text/event-stream')

@public_blueprint.route('/api/v1/get_response_stream_public', methods=['POST'])
def get_response_public():
    current_user_email = 'user@public.com'
    response = config.user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    data = request.get_json()
    user_input = data['user_input']
    topic_id = data['id']
    response = config.topics_table.get_item(
            Key={
                'userId': current_user_email,
                'topics_id': topic_id,
            }
            )
    topic = response['Item']
    
    if len(topic.get('messages',[])) >= config.maximum_chat_messages_without_login:
        response = {
            "error": "You need to sign in to continue the conversation.",
            "SigninError": True
        }
        return make_response(jsonify(response), 403)

    ta = TeachingAssistant_stream(
        api_keys=config.API_KEYS,
        conversation_model = config.conversation_model,
        extraction_model = config.extraction_model,
        temperature=0.4,
        max_tokens=5000
        )
    return Response(ta.handle_message(user_input, user['email'], topic_id), mimetype='text/event-stream')



@public_blueprint.route('/api/v1/wizard_details_public', methods=['GET'])
def wizard_details_public():
    try:
        # Generate a random seed for variety
        seed = str(random.randint(1, 10000))
        image_url = f'https://api.dicebear.com/7.x/avataaars/svg?seed={seed}'
        
        return jsonify({
            'image': image_url,
            'name': 'Tutor Creator'
        }), 200
            
    except Exception as e:
        logger.error("Error generating avatar: %s", str(e))
        return jsonify({'error': 'Service unavailable'}), 500

@public_blueprint.route('/api/v1/buddy_details_public', methods=['GET'])
def buddy_details_public():
    try:
        # Generate a random seed for variety
        seed = str(random.randint(1, 10000))
        
        # Using a different style for buddy to differentiate from wizard
        image_url = f'https://api.dicebear.com/7.x/bottts/svg?seed={seed}'  # Using bottts style for robot-like tutor
        # Or keep avataaars with different options:
        # image_url = f'https://api.dicebear.com/7.x/avataaars/svg?seed={seed}&backgroundColor=lightblue&mood=happy'
        
        return jsonify({
            'image': image_url,
            'name': 'Tutor'
        }), 200
            
    except Exception as e:
        logger.error("Error generating avatar: %s", str(e))
        return jsonify({'error': 'Service unavailable'}), 500



@public_blueprint.route('/api/v1/Get_created_topic_public', methods=['POST'])
def get_created_topic_public():
    current_user_email = 'user@public.com'
    data = request.get_json()
    conv_id = data['id']
    conv = config.conversations_table.get_item(
        Key={
                    'conv_id':conv_id, 
                }
    )['Item']
    topic_id = conv.get('topic_id')
    last_topic = config.topics_table.get_item(
            Key={
                    'userId': current_user_email,  # replace with your userId
                    'topics_id': topic_id  # replace with your topicId
                }
            )['Item']
    category = last_topic.get('category', "1")
    icons = config.asset_table.get_item(
            Key={
                    'asset_name': 'icon',  # replace with your userId
                })['Item']
    return jsonify({
        "Topic": last_topic['topic'], 
        "Goal": last_topic['goal'], 
        "id": topic_id, 
        "lang_id": last_topic['langid'], 
        "lang_name": last_topic["lang_name"], 
        "monaco_name": last_topic["monaco_name"], 
        'icon' : icons.get(category, icons['1'])  
        })


@public_blueprint.route('/api/v1/assign_topic_to_user', methods=['POST'])
def get_created_topic():
    current_user_email = get_jwt_identity()
    public_user_email = 'user@public.com'
    ## retrive topic
    data = request.get_json()
    topic_id = data['id']
    response = config.topics_table.get_item(
            Key={
                'userId': public_user_email,
                'topics_id': topic_id,
            }
            )
    topic = response['Item']
    ## update topic
    topic['userId'] = current_user_email 
    config.topics_table.put_item(Item=topic)
    config.user_table.update_item(
        Key={
            'email': current_user_email,  # replace with the actual userId
        },
        UpdateExpression="SET created_topics = list_append(created_topics, :i)",
        ExpressionAttributeValues={
            ':i': [topic_id],  # replace with the actual new topic ID
        },
        ReturnValues="UPDATED_NEW"
    )

    return jsonify({'message': 'Success'}), 200
