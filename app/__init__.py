import os
from flask import Flask


def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY='minecraft_manager_secret_key',
        DOCKER_COMPOSE_FILE=os.environ.get('DOCKER_COMPOSE_FILE', 'docker-compose.yml'),
        WORLDS_DIR=os.environ.get('WORLDS_DIR', 'worlds'),
        CONTAINER_NAME='minecraft'
    )

    # Override config with instance config
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register blueprints
    from app.routes import main, world
    app.register_blueprint(main.bp)
    app.register_blueprint(world.bp)

    # No need to add url_rule for index in this app

    return app
