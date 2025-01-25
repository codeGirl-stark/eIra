from .settings import *

ALLOWED_HOSTS = ['*']
DEBUG = True
TEMPLATES_DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY')
