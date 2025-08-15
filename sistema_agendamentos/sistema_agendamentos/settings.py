# D:\sistema_agendamentos\sistema_agendamentos\sistema_agendamentos\settings.py
# VERSÃO ATUALIZADA PARA PRODUÇÃO

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CONFIGURAÇÕES DE PRODUÇÃO ---
# Estamos usando variáveis de ambiente (que configuraremos no painel da Hostinger)
# para manter nossas chaves e senhas seguras.

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-sua-chave-local-para-desenvolvimento')

# DEBUG será 'True' localmente, mas 'False' no servidor da Hostinger
# A variável de ambiente DJANGO_DEBUG no servidor será definida como 'False'
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Adicione aqui o seu domínio quando o tiver. Ex: 'meusite.com.br', 'www.meusite.com.br'
# A variável de ambiente será uma string separada por vírgulas.
ALLOWED_HOSTS_ENV = os.environ.get('DJANGO_ALLOWED_HOSTS')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',')
else:
    ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sistema_agendamentos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Se você tiver uma pasta 'templates' na raiz do projeto, adicione aqui:
        # 'DIRS': [BASE_DIR / 'templates'],
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema_agendamentos.wsgi.application'


# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
# Este código verifica se estamos no ambiente de produção (usando as variáveis
# da Hostinger) e usa o MySQL. Caso contrário, usa o SQLite local.

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')

if DB_NAME:
    # Configuração para o banco de dados de produção (MySQL na Hostinger)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': '3306',
        }
    }
else:
    # Configuração para o banco de dados de desenvolvimento (local)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# --- CONFIGURAÇÃO DE ARQUIVOS ESTÁTICOS E DE MÍDIA ---
# Esta seção é CRUCIAL para produção.

STATIC_URL = 'static/'
# Onde o Django vai procurar por arquivos estáticos que não estão dentro de uma app.
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
# Onde o comando 'collectstatic' vai copiar TODOS os arquivos estáticos para o servidor.
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações de Login/Logout
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'