from flask import Blueprint, request, jsonify
from .models import db, User, Tweet

bp = Blueprint('routes', __name__)

def error_response(error_type, message, status_code=400):
    return jsonify({
        "result": False,
        "error_type": error_type,
        "error_message": message
    }), status_code

def get_current_user(api_key):
    if not api_key:
        return None
    return User.query.filter_by(api_key=api_key).first()

def require_auth(f):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('api-key')
        if not api_key:
            return error_response("Authentication", "API key is required", 401)
        user = get_current_user(api_key)
        if not user:
            return error_response("Authentication", "Invalid API key", 401)
        return f(user, *args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@bp.route('/api/tweets', methods=['POST'])
@require_auth
def create_tweet(user):
    data = request.get_json()
    if not data or 'tweet_data' not in data:
        return error_response("Validation", "Missing tweet data")
    tweet = Tweet(content=data['tweet_data'], user_id=user.id)
    db.session.add(tweet)
    db.session.commit()
    return jsonify({"result": True, "tweet_id": tweet.id})

@bp.route('/api/tweets', methods=['GET'])
@require_auth
def get_feed(user):
    tweets = Tweet.query.order_by(Tweet.created_at.desc()).limit(10).all()
    return jsonify({
        "result": True,
        "tweets": [{
            "id": t.id,
            "content": t.content,
            "author": {"id": t.author.id, "name": t.author.name}
        } for t in tweets]
    })
