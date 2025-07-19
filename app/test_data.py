from . import db
from .models import User, Tweet, Follow, Like, Media


def create_test_data():
    # Создаем пользователей
    users = [
        User(name="John Doe", api_key="john_api_key"),
        User(name="Jane Smith", api_key="jane_api_key"),
        User(name="Bob Johnson", api_key="bob_api_key"),
        User(name="Test User", api_key="test")
    ]

    for user in users:
        db.session.add(user)
    db.session.commit()

    # Создаем подписки
    follow1 = Follow(follower_id=users[0].id, followed_id=users[1].id)
    follow2 = Follow(follower_id=users[0].id, followed_id=users[2].id)
    follow3 = Follow(follower_id=users[3].id, followed_id=users[0].id)

    db.session.add_all([follow1, follow2, follow3])
    db.session.commit()

    # Создаем твиты
    tweets = [
        Tweet(content="Hello world!", user_id=users[0].id),
        Tweet(content="Just setting up my Twitter clone", user_id=users[0].id),
        Tweet(content="My first tweet", user_id=users[1].id),
        Tweet(content="Another tweet from Jane", user_id=users[1].id),
        Tweet(content="Bob here, what's up?", user_id=users[2].id),
        Tweet(content="Test tweet from Test User", user_id=users[3].id),
        Tweet(content="This is a test tweet", user_id=users[3].id),
        Tweet(content="More content for testing", user_id=users[3].id),
        Tweet(content="Testing pagination - 1", user_id=users[3].id),
        Tweet(content="Testing pagination - 2", user_id=users[3].id),
        Tweet(content="Testing pagination - 3", user_id=users[3].id),
        Tweet(content="Testing pagination - 4", user_id=users[3].id),
        Tweet(content="Testing pagination - 5", user_id=users[3].id),
        Tweet(content="Testing pagination - 6", user_id=users[3].id),
        Tweet(content="Testing pagination - 7", user_id=users[3].id),
    ]

    for tweet in tweets:
        db.session.add(tweet)
    db.session.commit()

    # Добавляем лайки
    for i, tweet in enumerate(tweets):
        # Каждый пользователь лайкает каждый третий твит
        for j, user in enumerate(users):
            if (i + j) % 3 == 0:
                like = Like(user_id=user.id, tweet_id=tweet.id)
                db.session.add(like)

    db.session.commit()

    print("Test data created successfully")