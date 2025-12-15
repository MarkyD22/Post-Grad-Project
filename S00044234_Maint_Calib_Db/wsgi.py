"""
WSGI config for S00044234_Maint_Calib_Db project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'S00044234_Maint_Calib_Db.settings')

application = get_wsgi_application()
