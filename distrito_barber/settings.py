from pathlib import Path
import environ
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Leer variables de entorno desde .env
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# Seguridad
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    # Apps del proyecto
    'core',
    'seguridad',
    'services.apps.ServicesConfig',
    'barbers.apps.BarbersConfig',
    'appointments.apps.AppointmentsConfig',
    'website.apps.WebsiteConfig',
    'dashboard.apps.DashboardConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'seguridad.middleware.ForzarCambioPasswordMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'distrito_barber.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'core.context_processors.identidad_barberia',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'distrito_barber.wsgi.application'


# PostgreSQL para desarrollo local. Configurar DATABASE_URL en .env.
# No volver silenciosamente a SQLite si falta la configuración.
DATABASES = {'default': env.db('DATABASE_URL')}
if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise ImproperlyConfigured('DATABASE_URL debe apuntar a PostgreSQL.')


# Validacion de contrasenas
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internacionalizacion
LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/El_Salvador'

USE_I18N = True

USE_TZ = True


# Archivos estaticos
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'seguridad.Usuario'

# Autenticacion
LOGIN_URL = '/seguridad/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/seguridad/login/'

# Mapeo de etiquetas de mensajes a clases de Bootstrap
from django.contrib.messages import constants as messages_const
MESSAGE_TAGS = {
    messages_const.DEBUG: 'secondary',
    messages_const.INFO: 'info',
    messages_const.SUCCESS: 'success',
    messages_const.WARNING: 'warning',
    messages_const.ERROR: 'danger',
}

# Identidad provisional; puede cambiarse sin editar las pantallas.
NOMBRE_BARBERIA = env("NOMBRE_BARBERIA", default="Distrito Barber")
