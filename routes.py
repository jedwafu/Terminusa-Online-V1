from flask import jsonify, request
from app import app, db
from models import User, Transaction, ChatMessage
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

# Health check route
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

# User routes
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'level': user.level,
            'is_active': user.is_active
        } for user in users])
    except Exception as e:
        logging.error(f"Error getting users: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'level': user.level,
            'is_active': user.is_active
        })
    except Exception as e:
        logging.error(f"Error getting user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Transaction routes
@app.route('/api/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    try:
        user_id = get_jwt_identity()
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        return jsonify([{
            'id': tx.id,
            'type': tx.type,
            'amount': tx.amount,
            'currency': tx.currency,
            'description': tx.description,
            'transaction_metadata': tx.transaction_metadata,
            'created_at': tx.created_at.isoformat()
        } for tx in transactions])
    except Exception as e:
        logging.error(f"Error getting transactions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Chat routes
@app.route('/api/messages', methods=['GET'])
@jwt_required()
def get_messages():
    try:
        channel = request.args.get('channel', 'global')
        messages = ChatMessage.query.filter_by(channel=channel).order_by(ChatMessage.created_at.desc()).limit(50).all()
        return jsonify([{
            'id': msg.id,
            'sender_id': msg.sender_id,
            'channel': msg.channel,
            'content': msg.content,
            'message_metadata': msg.message_metadata,
            'created_at': msg.created_at.isoformat()
        } for msg in messages])
    except Exception as e:
        logging.error(f"Error getting messages: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/messages', methods=['POST'])
@jwt_required()
def send_message():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        message = ChatMessage(
            sender_id=user_id,
            channel=data.get('channel', 'global'),
            content=data['content'],
            message_metadata=data.get('metadata', {})
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'id': message.id,
            'sender_id': message.sender_id,
            'channel': message.channel,
            'content': message.content,
            'message_metadata': message.message_metadata,
            'created_at': message.created_at.isoformat()
        })
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
