from app import create_app
from app.test_data import create_test_data
import os

app = create_app()

if os.environ.get('FLASK_ENV') == 'development':
    with app.app_context():
        from app.models import User
        if not User.query.first():
            create_test_data()
            print("Test data initialized")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)