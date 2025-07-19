from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
import os

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__, static_folder='../static', static_url_path='/')

    # Конфигурация
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
                                                           'postgresql://user:password@db:5432/microblog')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '../uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Swagger
    SWAGGER_URL = '/api/apidocs'
    API_URL = '/api/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Microblog API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Регистрация маршрутов
    from . import routes
    app.register_blueprint(routes.bp)

    # Создание папки для загрузок
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app