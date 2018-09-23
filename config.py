import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    DEBUG = os.environ.get("FLASK_DEBUG") is not None

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = [os.environ.get('ADMINS'), "no-reply@shopify.ca"]

    ADMIN_KEY = os.environ.get("ADMIN_KEY")

    # by default, reqparse of the flask restful extension would return an erorr as soon as it finds an invalid input
    # but if we set bundle errors to true, the error would be returned after all inputs have been evaluated
    BUNDLE_ERRORS = True


