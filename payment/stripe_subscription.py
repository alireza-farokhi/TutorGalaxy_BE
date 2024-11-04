from flask import Flask, render_template, request, jsonify, Blueprint
import stripe
from dotenv import load_dotenv
import os
from config import user_table
from stripe.error import SignatureVerificationError
from datetime import datetime, timedelta
from tinydb import Query
import logging

# Create a logger for this file
logger = logging.getLogger(__name__)

payments_blueprint = Blueprint('payments', __name__)

load_dotenv()

stripe.api_key = os.environ.get("secret_key")
stripe_webhook_secret = os.environ.get('webhook_secret')

@payments_blueprint.route('/v1/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.json
    current_user_email = request.args.get('email')
    User_Query = Query()
    user = user_table.get(User_Query.email == current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if user.get('subscribed', {}).get('state', False):
        return jsonify({"message": "User is already subscribed"}), 400
    
    if not user.get('active_checkout_session'):
        logger.info('Creating new checkout session for user: %s', current_user_email)
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        user_table.update(
            {
                'active_checkout_session': {
                    'session_id': None,
                    'timestamp': current_time
                }
            },
            User_Query.email == current_user_email
        )
        user = user_table.get(User_Query.email == current_user_email)

    default_url = 'https://vocoverse.com'
    success_url = data.get('success_url', default_url)  
    cancel_url = data.get('cancel_url', default_url)
    if not success_url.startswith(('http://', 'https://')):
        success_url = 'https://' + success_url
    if not cancel_url.startswith(('http://', 'https://')):
        cancel_url = 'https://' + cancel_url
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user_email,
            line_items=[{
                'price': os.environ.get("price_id"),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )

        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        user_table.update(
            {
                'active_checkout_session': {
                    'session_id': checkout_session.id,
                    'timestamp': current_time
                }
            },
            User_Query.email == current_user_email
        )

        return jsonify({'url': checkout_session.url})
    except Exception as e:
        logger.error('Error creating checkout session: %s', str(e))
        return jsonify(error=str(e)), 500

@payments_blueprint.route('/v1/manage-subscription', methods=['POST'])
def manage_subscription():
    current_user_email = request.args.get('email')
    data = request.json

    User_Query = Query()
    user = user_table.get(User_Query.email == current_user_email)
    
    if not user or not user.get('subscribed', {}).get('stripe_id'):
        return jsonify({'message': 'User not found or user is not a Stripe customer'}), 404

    stripe_customer_id = user['subscribed']['stripe_id']
    default_url = 'your url'
    return_url = data.get('return_url', default_url)

    if not return_url.startswith(('http://', 'https://')):
        return_url = 'https://' + return_url

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url
        )
        return jsonify({'session_url': session.url}), 200
    except Exception as e:
        logger.error('Error creating billing portal session: %s', str(e))
        return jsonify({'error': str(e)}), 500









    
