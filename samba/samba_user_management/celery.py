
from celery import Celery
import os

celery_broker = os.environ['RABBITMQ_HOST']
broker_port = os.environ['RABBITMQ_PORT']
broker_user = os.environ['RABBITMQ_USER']
broker_password = os.environ['RABBITMQ_PASSWORD']
broker_vhost = os.environ['RABBITMQ_VHOST']


broker_url = 'amqps://' + broker_user + ':' + broker_password + '@' + celery_broker + ':' + broker_port + '/' + broker_vhost
backend_url = 'rpc://' + broker_user + ':' + broker_password + '@' + celery_broker + ':' + broker_port + '/' + broker_vhost

app = Celery(
    'samba_user_management_tasks',
    broker=broker_url,
    backend=backend_url,
    broker_use_ssl = {
        'keyfile': '/opt/certificates/rabbitmq_serverclient_key.pem',
        'certfile': '/opt/certificates/rabbitmq_serverclient_cert.pem',
        'ca_certs': '/opt/certificates/rabbitmq_cacert.pem',
        'cert_reqs': True
    },
    include = ['samba_user_management.tasks']
)

app.conf.update(
    BROKER_HEARTBEAT=10,
    BROKER_HEARTBEAT_CHECKRATE=2.0,
    CELERY_RESULT_EXPIRES=3600,
)

