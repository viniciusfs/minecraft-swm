import os
from flask import Flask

from app.routes import main


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='minecraft_manager_secret_key',
        DOCKER_COMPOSE_FILE=os.environ.get('DOCKER_COMPOSE_FILE', 'docker-compose.yml'),
        WORLDS_DIR=os.environ.get('WORLDS_DIR', 'worlds'),
        CONTAINER_NAME='minecraft'
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(main.bp)

    return app
