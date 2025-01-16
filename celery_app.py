import os

from celery import Celery

celery_app = Celery(
    'my_project',
    broker=os.environ.get('CELERY_BROKER_URL'),  # MongoDB as the broker
    backend=os.environ.get('CELERY_BROKER_URL')  # MongoDB as the result backend
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
celery_app.autodiscover_tasks(['api.deployments'])
