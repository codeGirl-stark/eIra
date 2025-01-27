import os
from dotenv import load_dotenv

load_dotenv()

DATABASES = {
    'default': {
        'ENGINE': os.getenv("ENGINE"),
        'NAME': os.getenv("NAME"),
        'USER': os.getenv("USER"), # le user de mon localhost
        'PASSWORD': os.getenv("PASSWORD"), # le password de mon localhost 
        'HOST': os.getenv("HOST"),  # Ou spécifiez l'adresse IP ou le nom d'hôte du serveur MySQL
        'PORT': os.getenv("PORT"),  # Le port par défaut de MySQL est 3306
    }
}