import logging
import os
from flask import Flask

from .extensions import bootstrap, ckeditor, login_manager, gravatar, db
from .routes import main
from .models import Base

logging.basicConfig(level=logging.INFO)


def create_app():
    missing = [var for var in [
        'GMAIL_SMTP_ADDRESS',
        'GMAIL_SMTP_EMAIL',
        'GMAIL_SMTP_PASSWORD',
        'FLASK_KEY'
    ] if not os.environ.get(var)]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )
    app.config['SECRET_KEY'] = os.environ['FLASK_KEY']
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL', 'sqlite:///posts.db')

    bootstrap.init_app(app)
    ckeditor.init_app(app)
    login_manager.init_app(app)
    gravatar.init_app(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main)

    return app

