from flask import Flask, request, jsonify
from functools import wraps
from database.models import Database
from database.config import SECRET_KEY
import jwt
import datetime
import uuid

app = Flask(__name__)
db = Database()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = db.verify_user(data['email'], data['password'])
            if not current_user:
                return jsonify({'message': 'Invalid token!'}), 401
        except:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not all(k in data for k in ['email', 'password', 'first_name', 'last_name']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    user_id = db.create_user(
        data['email'],
        data['password'],
        data['first_name'],
        data['last_name'],
        data.get('phone')
    )
    
    if user_id is None:
        return jsonify({'message': 'Email already exists'}), 400
    
    return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not all(k in data for k in ['email', 'password']):
        return jsonify({'message': 'Missing email or password'}), 400
    
    user_id = db.verify_user(data['email'], data['password'])
    if not user_id:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({
        'email': data['email'],
        'password': data['password'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY)
    
    return jsonify({'token': token, 'user_id': user_id})

@app.route('/api/generate-api-key', methods=['POST'])
@token_required
def generate_api_key(current_user):
    data = request.get_json()
    
    if 'name' not in data:
        return jsonify({'message': 'API key name is required'}), 400
    
    api_key = db.generate_api_key(current_user, data['name'])
    return jsonify({'api_key': api_key})

@app.route('/api/api-keys', methods=['GET'])
@token_required
def get_api_keys(current_user):
    api_keys = db.get_user_api_keys(current_user)
    return jsonify({'api_keys': api_keys})

@app.route('/api/deactivate-api-key/<int:api_key_id>', methods=['POST'])
@token_required
def deactivate_api_key(current_user, api_key_id):
    success = db.deactivate_api_key(api_key_id)
    if success:
        return jsonify({'message': 'API key deactivated successfully'})
    return jsonify({'message': 'API key not found'}), 404

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    
    if not all(k in data for k in ['first_name', 'last_name', 'email', 'subject', 'message']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    message_id = db.store_contact_message(
        data['first_name'],
        data['last_name'],
        data['email'],
        data.get('phone'),
        data['subject'],
        data['message']
    )
    
    return jsonify({'message': 'Message stored successfully', 'message_id': message_id}), 201

@app.route('/api/chatbot/message', methods=['POST'])
def chatbot_message():
    data = request.get_json()
    
    if not all(k in data for k in ['session_id', 'message']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Store user message
    message_id = db.store_chatbot_message(
        data['session_id'],
        'user',
        data['message'],
        data.get('user_id')  # Optional user_id for authenticated users
    )
    
    # Here you would typically process the message with your chatbot logic
    # For now, we'll just echo back a simple response
    bot_response = f"Echo: {data['message']}"
    
    # Store bot response
    bot_message_id = db.store_chatbot_message(
        data['session_id'],
        'bot',
        bot_response,
        data.get('user_id')
    )
    
    return jsonify({
        'message': 'Message stored successfully',
        'user_message_id': message_id,
        'bot_message_id': bot_message_id,
        'response': bot_response
    }), 201

@app.route('/api/chatbot/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    limit = request.args.get('limit', default=50, type=int)
    history = db.get_chatbot_history(session_id, limit)
    
    formatted_history = []
    for msg in history:
        formatted_history.append({
            'id': msg[0],
            'user_id': msg[1],
            'message_type': msg[2],
            'message': msg[3],
            'created_at': msg[4]
        })
    
    return jsonify({'history': formatted_history})

@app.route('/api/chatbot/user-history', methods=['GET'])
@token_required
def get_user_chat_history(current_user):
    limit = request.args.get('limit', default=50, type=int)
    history = db.get_user_chatbot_history(current_user, limit)
    
    formatted_history = []
    for msg in history:
        formatted_history.append({
            'id': msg[0],
            'session_id': msg[1],
            'message_type': msg[2],
            'message': msg[3],
            'created_at': msg[4]
        })
    
    return jsonify({'history': formatted_history})

if __name__ == '__main__':
    app.run(debug=True) 