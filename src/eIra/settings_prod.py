import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_HOSTS = ['*']
# DEBUG = True

# TEMPLATES_DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': os.getenv("ENGINE"),
        'NAME': os.getenv("NAME"),
        'USER': os.getenv("USER"), # le user de mon localhost
        'PASSWORD': os.getenv("PASSWORD"), # le password de mon localhost
        'HOST': os.getenv("HOST"),  # Ou spécifiez l'adresse IP ou le nom d'hôte du serveur MySQL
        'PORT': os.getenv("PORT"),
        'OPTIONS': {
            'init_command': os.getenv('OPTIONS', default="SET sql_mode='STRICT_TRANS_TABLES'"),
        }
    }
}