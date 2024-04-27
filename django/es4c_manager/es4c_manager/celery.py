import os

from django.conf import settings

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'es4c_manager.settings')

app = Celery(
    'samba_user_management_tasks',
    broker = settings.CELERY_BROKER_URL,
    backend = settings.CELERY_RESULT_BACKEND,
    broker_use_ssl = {
        'keyfile': '/opt/certificates/rabbitmq_serverclient_key.pem',
        'certfile': '/opt/certificates/rabbitmq_serverclient_cert.pem',
        'ca_certs': '/opt/certificates/rabbitmq_cacert.pem',
        'cert_reqs': True
    },
    include = ['main.tasks']
)

app.conf.update(
    BROKER_HEARTBEAT=10,
    BROKER_HEARTBEAT_CHECKRATE=2.0,
    CELERY_RESULT_EXPIRES=3600
)

app.autodiscover_tasks()
