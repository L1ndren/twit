from flask import Blueprint, request, jsonify, current_app, send_from_directory, send_file
from werkzeug.utils import secure_filename
from .models import db, User, Tweet, Media, Like, Follow
import os
import uuid
from datetime import datetime

bp = Blueprint('routes', __name__)


def get_current_user(api_key):
    return User.query.filter_by(api_key=api_key).first()


def error_response(error_type, message, status_code=400):
    return jsonify({
        "result": False,
        "error_type": error_type,
        "error_message": message
    }), status_code


@bp.route('/api/swagger.json')
def swagger():
    return send_file('../swagger.json')


@bp.route('/')
def serve_frontend():
    return send_from_directory(current_app.static_folder, 'index.html')


@bp.route('/<path:path>')
def serve_static(path):
    return send_from_directory(current_app.static_folder, path)


@bp.route('/api/tweets', methods=['POST'])
def create_tweet():
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    data = request.get_json()
    if not data or 'tweet_data' not in data:
        return error_response("Validation", "Missing tweet data")

    tweet = Tweet(
        content=data['tweet_data'],
        user_id=user.id
    )

    db.session.add(tweet)

    # Прикрепление медиа
    media_ids = data.get('tweet_media_ids', [])
    for media_id in media_ids:
        media = Media.query.get(media_id)
        if media and media.user_id == user.id:
            tweet.media.append(media)

    db.session.commit()

    return jsonify({
        "result": True,
        "tweet_id": tweet.id
    })


@bp.route('/api/medias', methods=['POST'])
def upload_media():
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    if 'file' not in request.files:
        return error_response("Validation", "No file part")

    file = request.files['file']
    if file.filename == '':
        return error_response("Validation", "No selected file")

    if file:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        media = Media(
            file_path=unique_filename,
            user_id=user.id
        )
        db.session.add(media)
        db.session.commit()

        return jsonify({
            "result": True,
            "media_id": media.id
        })

    return error_response("Upload", "File upload failed")


@bp.route('/api/tweets/<int:tweet_id>', methods=['DELETE'])
def delete_tweet(tweet_id):
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    tweet = Tweet.query.get(tweet_id)
    if not tweet:
        return error_response("Not Found", "Tweet not found", 404)

    if tweet.user_id != user.id:
        return error_response("Authorization", "You can only delete your own tweets", 403)

    db.session.delete(tweet)
    db.session.commit()

    return jsonify({"result": True})


@bp.route('/api/tweets/<int:tweet_id>/likes', methods=['POST'])
def like_tweet(tweet_id):
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    tweet = Tweet.query.get(tweet_id)
    if not tweet:
        return error_response("Not Found", "Tweet not found", 404)

    # Проверяем, не лайкал ли уже
    existing_like = Like.query.filter_by(
        user_id=user.id,
        tweet_id=tweet_id
    ).first()

    if existing_like:
        return jsonify({"result": True})

    like = Like(user_id=user.id, tweet_id=tweet_id)
    db.session.add(like)
    db.session.commit()

    return jsonify({"result": True})


@bp.route('/api/tweets/<int:tweet_id>/likes', methods=['DELETE'])
def unlike_tweet(tweet_id):
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    like = Like.query.filter_by(
        user_id=user.id,
        tweet_id=tweet_id
    ).first()

    if not like:
        return jsonify({"result": True})

    db.session.delete(like)
    db.session.commit()

    return jsonify({"result": True})


@bp.route('/api/users/<int:user_id>/follow', methods=['POST'])
def follow_user(user_id):
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    if user.id == user_id:
        return error_response("Validation", "Cannot follow yourself")

    target_user = User.query.get(user_id)
    if not target_user:
        return error_response("Not Found", "User not found", 404)

    # Проверяем, не подписан ли уже
    existing_follow = Follow.query.filter_by(
        follower_id=user.id,
        followed_id=user_id
    ).first()

    if existing_follow:
        return jsonify({"result": True})

    follow = Follow(follower_id=user.id, followed_id=user_id)
    db.session.add(follow)
    db.session.commit()

    return jsonify({"result": True})


@bp.route('/api/users/<int:user_id>/follow', methods=['DELETE'])
def unfollow_user(user_id):
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    follow = Follow.query.filter_by(
        follower_id=user.id,
        followed_id=user_id
    ).first()

    if not follow:
        return jsonify({"result": True})

    db.session.delete(follow)
    db.session.commit()

    return jsonify({"result": True})


@bp.route('/api/tweets', methods=['GET'])
def get_feed():
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    # Получаем параметры пагинации
    limit = request.args.get('limit', default=5, type=int)
    offset = request.args.get('offset', default=0, type=int)

    # Получаем ID пользователей, на которых подписан текущий пользователь
    following_ids = [f.followed_id for f in user.following.all()]
    following_ids.append(user.id)  # Добавляем свои твиты

    # Запрос для получения ленты с пагинацией
    tweets_query = Tweet.query.filter(Tweet.user_id.in_(following_ids)) \
        .order_by(Tweet.created_at.desc())

    total_tweets = tweets_query.count()
    tweets = tweets_query.offset(offset).limit(limit).all()

    # Формируем ответ
    response_tweets = []
    for tweet in tweets:
        author = User.query.get(tweet.user_id)
        media_links = [
            f"/api/media/{media.id}"
            for media in tweet.media
        ]

        likes = []
        for like in tweet.likes:
            user_like = User.query.get(like.user_id)
            likes.append({
                "user_id": user_like.id,
                "name": user_like.name
            })

        response_tweets.append({
            "id": tweet.id,
            "content": tweet.content,
            "attachments": media_links,
            "author": {
                "id": author.id,
                "name": author.name
            },
            "likes": likes
        })

    return jsonify({
        "result": True,
        "tweets": response_tweets,
        "total": total_tweets,
        "limit": limit,
        "offset": offset
    })


@bp.route('/api/users/me', methods=['GET'])
def get_current_user_profile():
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    return get_user_profile(user.id)


@bp.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    api_key = request.headers.get('api-key')
    current_user = get_current_user(api_key)
    if not current_user:
        return error_response("Authentication", "Invalid API key", 401)

    user = User.query.get(user_id)
    if not user:
        return error_response("Not Found", "User not found", 404)

    followers = []
    for follow in user.followers:
        follower = User.query.get(follow.follower_id)
        followers.append({
            "id": follower.id,
            "name": follower.name
        })

    following = []
    for follow in user.following:
        followed = User.query.get(follow.followed_id)
        following.append({
            "id": followed.id,
            "name": followed.name
        })

    return jsonify({
        "result": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": followers,
            "following": following
        }
    })


@bp.route('/api/media/<int:media_id>', methods=['GET'])
def get_media(media_id):
    media = Media.query.get(media_id)
    if not media:
        return error_response("Not Found", "Media not found", 404)

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.file_path)
    return send_file(file_path)

@bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@bp.route('/api/users/me/api-key', methods=['PUT'])
def update_api_key():
    api_key = request.headers.get('api-key')
    user = get_current_user(api_key)
    if not user:
        return error_response("Authentication", "Invalid API key", 401)

    data = request.get_json()
    if not data or 'new_api_key' not in data:
        return error_response("Validation", "Missing new API key")

    new_key = data['new_api_key']

    # Проверяем, не занят ли ключ другим пользователем
    existing_user = User.query.filter_by(api_key=new_key).first()
    if existing_user and existing_user.id != user.id:
        return error_response("Conflict", "API key already in use", 409)

    user.api_key = new_key
    db.session.commit()

    return jsonify({
        "result": True,
        "message": "API key updated successfully"
    })