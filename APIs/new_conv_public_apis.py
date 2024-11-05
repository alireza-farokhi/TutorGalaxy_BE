from flask import request, jsonify, Blueprint, Response, make_response
from tutor_agent.Conv_handler_improved_mem import TeachingAssistant_stream
from init_agent.Conv_Creator_basics import ConvCreator_stream
import config
from tinydb import Query
from datetime import datetime
import pytz
import uuid 
import logging
import random

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
    User_Query = Query()
    user = config.user_table.get(User_Query.email == current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404

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
    User_Query = Query()
    user = config.user_table.get(User_Query.email == current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    user_input = data['user_input']
    topic_id = data['id']
    
    Topic_Query = Query()
    topic = config.topics_table.get(
        (Topic_Query.userId == current_user_email) & 
        (Topic_Query.topics_id == topic_id)
    )
    if not topic:
        return jsonify({"error": "Topic not found"}), 404
    
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
    
    Conv_Query = Query()
    conv = config.conversations_table.get(Conv_Query.conv_id == conv_id)
    if not conv:
        logger.error(f"Conversation not found: {conv_id}")
        return jsonify({"error": "Conversation not found"}), 404
        
    topic_id = conv.get('topic_id')
    Topic_Query = Query()
    last_topic = config.topics_table.get(
        (Topic_Query.userId == current_user_email) & 
        (Topic_Query.topics_id == topic_id)
    )
    if not last_topic:
        logger.error(f"Topic not found: {topic_id}")    
        return jsonify({"error": "Topic not found"}), 404

    category = last_topic.get('category', "1")
    Asset_Query = Query()
    icons = config.asset_table.get(Asset_Query.asset_name == 'icon')

    # Ensure icons is a dictionary and handle missing keys gracefully
    if not isinstance(icons, dict):
        icons = {}

    icon_value = icons.get(category, icons.get('1', None))

    return jsonify({
        "Topic": last_topic['topic'], 
        "Goal": last_topic['goal'], 
        "id": topic_id, 
        "lang_id": last_topic['langid'], 
        "lang_name": last_topic["lang_name"], 
        "monaco_name": last_topic["monaco_name"], 
        'icon': icon_value
    })

@public_blueprint.route('/api/v1/assign_topic_to_user', methods=['POST'])
def get_created_topic():
    current_user_email = request.args.get('email')  
    public_user_email = 'user@public.com'
    data = request.get_json()
    topic_id = data['id']
    
    Topic_Query = Query()
    topic = config.topics_table.get(
        (Topic_Query.userId == public_user_email) & 
        (Topic_Query.topics_id == topic_id)
    )
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # Update topic's userId
    topic['userId'] = current_user_email 
    config.topics_table.upsert(topic, 
        (Topic_Query.userId == current_user_email) & 
        (Topic_Query.topics_id == topic_id)
    )
    
    # Update user's created_topics
    User_Query = Query()
    user = config.user_table.get(User_Query.email == current_user_email)
    if user:
        created_topics = user.get('created_topics', [])
        created_topics.append(topic_id)
        config.user_table.update({'created_topics': created_topics}, User_Query.email == current_user_email)

    return jsonify({'message': 'Success'}), 200
