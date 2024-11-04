from flask import request, jsonify, Blueprint, make_response
from tinydb import Query
from config import *

page_wise_chat_history_blueprint = Blueprint('page_wise_chat_history', __name__)

@page_wise_chat_history_blueprint.route('/api/v1/page_wise_chat_history', methods=['POST'])
def get_page_wise_chat_history():
    data = request.get_json()

    # Check if email is in request
    
    current_user_email = data.get('email') or request.args.get('email')  
    if not current_user_email:
        return jsonify({"error": "User not found"}), 400
    
    topic_id = data.get('id')
    page_number = data.get('page_number', 0)

    # Get user data
    User = Query()
    user = user_table.get(User.email == current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get topic data
    try:
        Topic = Query()
        topic = topics_table.get(
            (Topic.userId == current_user_email) & 
            (Topic.topics_id == topic_id)
        )
    except Exception as e:
        return jsonify({"error": f"Error getting topic: {e}"}), 500

    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # Extract topic information
    topic_topic = topic['topic']
    topic_goal = topic['goal']
    topic_state = topic['state']
    topic_langid = topic.get('langid', "-1")
    topic_langname = topic.get('lang_name', "-1")
    topic_monaconame = topic.get('monaco_name', "-1")

    # Get messages for this topic
    try:
        Message = Query()
        all_messages = message_table.search(Message.topics_id == topic_id)
        
        # Sort messages by message_id (assuming it's a timestamp or sequential number)
        all_messages.sort(key=lambda x: x['message_id'], reverse=True)
        
        # Implement pagination
        start_idx = page_number * message_per_page
        end_idx = start_idx + message_per_page
        page_messages = all_messages[start_idx:end_idx]
        
        # Extract just the message content from each message document
        page_messages = [msg['message'] for msg in page_messages]
        
    except Exception as e:
        return jsonify({"error": f"Error getting messages: {e}"}), 500

    response_data = {
        "topic": topic_topic,
        "goal": topic_goal,
        "page": page_messages,
        "state": topic_state,
        "lang_id": topic_langid,
        "lang_name": topic_langname,
        "monaco_name": topic_monaconame,
        'message_per_page': message_per_page,
    }
    
    return make_response(jsonify(response_data), 200)