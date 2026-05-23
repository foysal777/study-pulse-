
import os

from decouple import config
from dotenv import load_dotenv 

import os
from pathlib import Path
from decouple import config
from dotenv import load_dotenv 
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$5h3i2#$qg#58b1)j00cluqvel2&rp_e^fp**(8f&xyl)!$l71'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

CSRF_TRUSTED_ORIGINS = [
    'https://formal-springer-chances-solely.trycloudflare.com',
    'https://grace-edition-prominent-blog.trycloudflare.com',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:7090',
    'http://127.0.0.1:6565',
    'http://localhost:8000',
    'http://localhost:7090',
    'http://localhost:6565',
    'https://*.ngrok-free.app',
]

# Application definition

INSTALLED_APPS = [
    "unfold",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'students',
    'teachers',
    'support',
    # framework 
    'rest_framework',
    "drf_spectacular",
      'rest_framework_simplejwt',
]

AUTH_USER_MODEL = "accounts.User"

UNFOLD = {
    "SITE_TITLE": "Study Pulse Admin",
    "SITE_HEADER": "Study Pulse",
    "SITE_SUBHEADER": "Management Dashboard",
    "SITE_SYMBOL": "dashboard",
    "DASHBOARD_CALLBACK": "common.dashboard_views.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "General",
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": "/admin/",
                    },
                    {
                        "title": "Pending Requests",
                        "icon": "notifications",
                        "link": "/admin/teachers/pendingrequest/",
                        "badge": "teachers.utils.get_pending_requests_count",
                    },
                ],
            },
            {
                "title": "Accounts",
                "items": [
                    {
                        "title": "Users",
                        "icon": "group",
                        "link": "/admin/accounts/user/",
                    },
                    {
                        "title": "One Time Passwords",
                        "icon": "vpn_key",
                        "link": "/admin/accounts/onetimepassword/",
                    },
                ],
            },
            {
                "title": "Students",
                "items": [
                    {
                        "title": "Student Profiles",
                        "icon": "person",
                        "link": "/admin/students/studentprofile/",
                    },
                    {
                        "title": "Assessment Templates",
                        "icon": "assignment",
                        "link": "/admin/students/assessmenttemplate/",
                    },
                    {
                        "title": "Assessment Questions",
                        "icon": "quiz",
                        "link": "/admin/students/assessmentquestion/",
                    },
                    
                    {
                        "title": "Student Assessment Attempts",
                        "icon": "history_edu",
                        "link": "/admin/students/studentassessmentattempt/",
                    },
                    {
                        "title": "Interest Summaries",
                        "icon": "auto_awesome",
                        "link": "/admin/students/interestsummary/",
                    },
                    {
                        "title": "Student Locations",
                        "icon": "location_on",
                        "link": "/admin/students/studentlocation/",
                    },
                ],
            },
            {
                "title": "Teachers",
                "items": [
                    {
                        "title": "Teachers List",
                        "icon": "school",
                        "link": "/admin/teachers/teacher/",
                    },
                    {
                        "title": "Teacher Profiles",
                        "icon": "badge",
                        "link": "/admin/teachers/teacherprofile/",
                    },
                    {
                        "title": "Teacher Availabilities",
                        "icon": "event_available",
                        "link": "/admin/teachers/teacheravailability/",
                    },
                    {
                        "title": "Teacher Slots",
                        "icon": "schedule",
                        "link": "/admin/teachers/teacherslot/",
                    },
                    {
                        "title": "Student Bookings",
                        "icon": "book_online",
                        "link": "/admin/teachers/studentbooking/",
                    },
                    {
                        "title": "Teachers Locations",
                        "icon": "location_on",
                        "link": "/admin/teachers/teacherslocation/",
                    },
                    {
                        "title": "Promotional Banner",
                        "icon": "menu_book",
                        "link": "/admin/students/recommendedcourse/",
                    },
                    {
                        "title": "Session List",
                        "icon": "view_list",
                        "link": "/admin/teachers/sessionlist/",
                    },
                    {
                        "title": "General Info",
                        "icon": "info",
                        "link": "/admin/teachers/generalinfo/",
                    },
                ],
            },
            {
                "title": "Support",
                "items": [
                    {
                        "title": "Policies",
                        "icon": "policy",
                        "link": "/admin/support/policy/",
                    },
                    {
                        "title": "Help & Support",
                        "icon": "support_agent",
                        "link": "/admin/support/helpsupport/",
                    },
                    {
                        "title": "Play Store QR Codes",
                        "icon": "qr_code_2",
                        "link": "/admin/support/playstoreqrcode/",
                    },
                ],
            },
        ],
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Study Pulse API",
    "DESCRIPTION": "API documentation",
    "VERSION": "1.0.0",
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'project_root.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'teachers.context_processors.pending_requests_count',
            ],
        },
    },
]



from datetime import timedelta 

# put on your settings.py file below INSTALLED_APPS
REST_FRAMEWORK = {


    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=10),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME': timedelta(days=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME_LATE_USER': timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME_LATE_USER': timedelta(days=30),
}







# Email Configuration from .env file
EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)  
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')








WSGI_APPLICATION = 'project_root.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }




from decouple import config

DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
        "OPTIONS": {
            "options": f"-c search_path={config('DB_SCHEMA', default='public')}",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/


EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)  
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
