from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler, QueueHandler, QueueListener
from queue import Queue
import os


db = SQLAlchemy()
migrate = Migrate()
mail = Mail()


def create_app(config_class=Config):
    # create an app
    app = Flask(__name__)
    # add configuration variables to the app
    app.config.from_object(config_class)

    # fit the flask extensions to the specific configuration of this app
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # register blueprints
    from App.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from App.main import bp as main_bp
    app.register_blueprint(main_bp)

    from App.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    if not app.debug:
        if app.config['MAIL_SERVER']:

            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='ShopifyAPI Failure',
                credentials=auth, secure=secure)
            mail_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            q = Queue()
            q_handler = QueueHandler(q)
            q_handler.setLevel(logging.ERROR)
            listener = QueueListener(q, mail_handler)
            app.logger.addHandler(q_handler)
            listener.start()

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/Shopify.log', maxBytes=131072, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('SIR startup')

    return app

from App import models
