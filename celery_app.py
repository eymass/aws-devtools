import os
import sys

from celery import Celery

# Validate required environment variables
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')

if not CELERY_BROKER_URL:
    print("ERROR: CELERY_BROKER_URL environment variable is not set.")
    print("Please set it to your MongoDB connection string:")
    print('  export CELERY_BROKER_URL="mongodb://localhost:27017/celery"')
    sys.exit(1)

celery_app = Celery(
    'aws_devtools',
    broker=CELERY_BROKER_URL,  # MongoDB as the broker
    backend=CELERY_BROKER_URL  # MongoDB as the result backend
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
celery_app.autodiscover_tasks(['api.deployments'])
