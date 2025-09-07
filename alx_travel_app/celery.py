import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")

# Create the Celery application instance.
app = Celery("alx_travel_app")

# Load task modules from all registered Django app configs.
# This means Celery will look for a tasks.py file in each of your apps.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
