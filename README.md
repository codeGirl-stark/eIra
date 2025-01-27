DOCUMENTATION DE DÉPLOIEMENT SUR PYHTONANYWHERE

ETAPE 1 :
envoyer le projet sur github
---git init



ETAPE 2 :
Cloner le projet sur PYHTONANYWHERE
---git clone https://github.com/votre-repo(ici il s'agit du lien HTTPS du repo sur github)

ETAPE 3 :
Créez et activez un environnement virtuel Python 3.10, Remplacez testenv par le nom de votre choix:
---mkvirtualenv --python=/usr/bin/python3.10 testenv
---workon testenv

ETAPE 4 :
Installez les packages nécessaires depuis requirements.txt.
---pip install -r requirements.txt

ETAPE 5 :
Aller dans Web de l'interface PythonAnywhere
>>>Next
---Manual configuration ---Next
---Python 3.10 ---Next

ETAPE 6 :
Configuration Web

Dans l'interface de PythonAnywhere, accédez à l'onglet Web, créez une nouvelle application Web avec une configuration manuelle (assurez-vous de ne pas choisir l'option 'Django'), puis configurez les chemins comme suit :

# Source code: /home/Jazzmeen/eIra/src (Chemin vers le src)
# Working directory: /home/Jazzmeen/ (laisser comme tel sur l'interface)
# Virtual env: /home/Jazzmeen/.virtualenvs/env (chemin vers le env)

Les urls en bas vers les fichiers statics et media
##url : /media/   ###Directory : /home/Jazzmeen/eIra/src/media (chemin vers le dossier media)


ETAPE 7 :
Cliquer sur WSGI configuration file: /var/www/jazzmeen_pythonanywhere_com_wsgi.py (sur l'interface de l'application web)

Dans le fichier WSGI tout supprimer et mettre ceci

# Configuration WSGI:
import os
import sys

project_home = '/home/username/project'(chemin vers le src)
if project_home not in sys.path:
    sys.path.insert(0, project_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'(dossierquicontientlesettings.settings)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


ETAPE 8 : 
ALLOWED_HOSTS = [
  'y ajouter le host de l'application de pythonanywhere'
  ex: 'Jazzmeen.pythonanywhere.com'
]


####CREATION CONFIGURATION ET CONNEXION DE LA BASE DE DONNÉES AU PROJET 
ETAPE 1 :
---Aller sur PythonAnywhere et dans l'onglet databases
----Choisir MySQL
----Entrer le mot de passe et connecter le serveur de base de données
----Créer la base de données 

ETAPE 2 :
Aller dans settings du projet 

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Jazzmeen$eIra',
        'USER': 'Jazzmeen',
        'PASSWORD': 'Procedure2022',
        'HOST': 'Jazzmeen.mysql.pythonanywhere-services.com',
        'PORT': '3306',
        'OPTION':{
            'init_command':"SET_sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}

ETAPE 3 :
Aller dans __init__.py

import pymysql
pymysql.install_as_MySQLdb()

ETAPE 4 :
Faire les migrations
