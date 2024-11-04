from flask import Blueprint, request, jsonify, make_response
from config import user_table, topics_table, asset_table, max_topic_topics_WO_sub
from tinydb import Query
import logging

# Create a logger for this specific module
logger = logging.getLogger(__name__)

tutor_history_blueprint = Blueprint('tutor_history', __name__)

@tutor_history_blueprint.route('/api/v1/user_profile', methods=['GET'])
def get_user_profile():
    current_user_email = request.args.get('email')
    logger.info("User email: %s", current_user_email)
    
    # Get user using TinyDB Query
    User_Query = Query()
    user = user_table.get(User_Query.email == current_user_email)
    logger.info("User: %s", user)
    
    if not user:
        logger.error("User not found")
        return jsonify({"error": "User not found"}), 404

    subscribed = user.get('subscribed', {}).get('state', False)
    user_create_topic_permission = True
    if not subscribed:
        if len(user.get('created_topics', [])) >= max_topic_topics_WO_sub:
            user_create_topic_permission = False

    if user.get('created_topics'):
        # Get icons
        Topic_Query = Query()
        icons = asset_table.get(Query().asset_name == 'icon')
        
        # Get all topics for user
        topics = []
        for topic_id in user['created_topics']:
            topic = topics_table.get(
                (Topic_Query.userId == current_user_email) & 
                (Topic_Query.topics_id == topic_id)
            )
            if topic:
                topics.append(topic)

        # Reverse the list to match your original ordering
        topics.reverse()

        topics_goals = []
        for topic in topics:
            langid = topic.get('langid', "-1")
            langname = topic.get('lang_name', "-1")
            monaconame = topic.get('monaco_name', "-1")
            category = topic.get('category', "1")
            if category not in ['1','2','3','4']: 
                category = '1'

            current_topic = {
                'topic': topic['topic'],
                'goal': topic['goal'],
                'id': topic['topics_id'],
                'state': topic['state'],
                'lang_id': str(langid),
                'lang_name': str(langname),
                'monaco_name': monaconame,
                'create_topic_permission': user_create_topic_permission,
                'icon': icons.get(category, icons['1']) if icons else None,
            }
            topics_goals.append(current_topic)
            
        return make_response(jsonify(topics_goals), 200)
    else:
        print("no topics found for the user")
        return jsonify({"error": "No topics found for the user"}), 404