# ES4PS-Containers

ES4PS-Containers are the core element within the ES4PS platform since it makes it possible to run all necessary services to provide any organization with a system that supports users' self-registration in a Django / celery (rabbit mq) / samba configuration that makes everything work. 

Through a docker composition (docker-compose.yaml) and a .env files (all of these available after running es4ps-setup-wizard), when you start es4ps-containers, users can access a Django web application where they'll create their user accounts restricted to their company only (through domain e-mail addresses restrictions) and then when their accounts are created (or activated), users' creation (or activation) tasks are triggered by Django in a celery queue where workers in samba servers wait for tasks in this queue and run it whenever a task is available there.

Figure 1 shows the ES4PS-Containers architecture:

<figure>

![](./docs/img/es4ps-containers.drawio.svg)

<figcaption style="text-align: center;">
    Figure 1: ES4PS-Containers architecture.
</figcaption>

</figure>

As it possible to see in Figure 1, the following services exert essential roles for the system to work:

- **Django**: The Django web application is the main service that users interact with to create their accounts. It also triggers tasks in the celery queue when users' accounts are created or activated.
- **RabbitMQ**: The RabbitMQ service is the message broker that Django uses to send tasks to the celery queue.
- **Celery**: The Celery service is the task queue that Django uses to send tasks to samba servers.
- **Workers in AD/DC Samba Servers**: The workers in samba servers are the services that run tasks in the celery queue. These tasks are responsible for creating or activating users' accounts in the samba servers.

It's important to say that, for security reasons, users passwords are not stored in plain text in anywhere witihin the system. Instead, when a user self registrer in Django, before storing its data (username, e-mail, name, etc.) in the database, a task with this data and appended with the user password is sent securely to the celery queue, since the celery communication is encrypted in every step of the way.

When the task is received by the workers in samba servers, the data securely sent through celery is used to create or activate the user account in the samba server, through the recommended procedures by the samba documentation.

If you're interested in learning how users' registration (and creation / activation) works in the ES4PS platform, as well, in how how the platform works in general you can check:

- Django Custom User Model (CollegeUser) defined in [`.django/es4c_manager/main/models.py`](https://github.com/DiegoAscanio/es4ps-containers/blob/main/django/es4c_manager/main/models.py) file. This model is responsible for storing users' data in the database and ES4PS considers as necessary data for users: `username`, `email`, `first_name`, `last_name` and `password`, altough the `password` attribute is not handled in this model file. You need to understand this model if you're willing to customize the user data in your ES4PS flavor.

- Django Custom User Manager (CollegeUserManager) defined in [`.django/es4c_manager/main/managers.py`](https://github.com/DiegoAscanio/es4ps-containers/blob/main/django/es4c_manager/main/managers.py) file. This manager is responsible for creating users in the database and is used by the Django Custom User Model (CollegeUser) to create users in the database. Through this manager would be possible to send tasks to the celery queue when a user is created or activated, but this is not the case in ES4PS, since the tasks are sent in the views.py file through the views that handle the user creation and activation.

- Django Views defined in [`.django/es4c_manager/main/views.py`](https://github.com/DiegoAscanio/es4ps-containers/blob/main/django/es4c_manager/main/views.py) file. The views `register`, `update_user_attributes` and `verify_email` are the main components responsible for handling users' operations in the Django web application as well, for calling the distributed tasks (through celery) that create or activate users' accounts in the samba servers.

- Celery Tasks and Connection objects defined in [`.django/es4c_manager/main/tasks.py`](https://github.com/DiegoAscanio/es4ps-containers/blob/main/django/es4c_manager/main/tasks.py), [`.django/es4c_manager/es4c_manager/celery.py`](https://github.com/DiegoAscanio/es4ps-containers/blob/main/django/es4c_manager/es4c_manager/celery.py), [`./samba/samba_user_management/tasks.py`](https://github.com/DiegoAscanio/es4ps-containers/blob/main/samba/samba_user_management/tasks.py) and [`./samba/samba_user_management/celery.py`](https://github.com/DiegoAscanio/es4ps-containers/blob/main/samba/samba_user_management/celery.py) respectively.
    - Studying the celery documentation, as far as the author knows, it is necessary that both sender and worker knows the tasks for each other, in other ways, that the files that define the tasks needs to exist in both sender and worker. This is the reason why the tasks are defined in both Django and samba services.
        - If you read `tasks.py` file you'll see that the tasks defined are capable of creating, enabling, updating and deleting users in the samba servers through the samba python library.
    - In the `celery.py` files you'll see that the connections are defined securely through `broker_use_ssl` parameter in the Celery constructor. It's important to say that RabbitMQ SSL encrypted connections are estabilished through the 5671 TCP port and the necessary certificates (at least on this release) are generated in the first boot of the es4ps-containers composition by the `init-certificates` container.

- `docker-compose.yaml` file, responsible for the definition of all the containers necessary to provide the services that the ES4PS platform depends on. If you read this file you'll see that the first service defined is the `init-certificates`, responsible for generating the necessary certificates for RabbitMQ SSL connections, as well as the self-signed certificates that will encrypt HTTP connections between end users and the Django web application. This service will check everytime if certificates exist and if not will create them for the platform. A list for the remaining services is presented below:
    - `rabbitmq`: The RabbitMQ service is the message broker that Django uses to send (and samba workers to receive) tasks to the celery queue. It is a simple container and it's highly unlikely that you'll ever have to change anything in this service.
    - `samba`: This is the container that will run the SAMBA AD/DC server and the worker responsible for picking users' (registration, modification and deletion) tasks from the celery queue and run them to perform the necessary operations. In future releases it is expected that this container will suffer changes to support more services in the samba server, like file sharing and printing services. If you're willing to customize the samba server in your ES4PS flavor, you should start by studying the `samba/Dockerfile` and `samba/samba_user_management/tasks.py` files.
    - `django`: This is the container that will run the Django web application that users will interact with to create their accounts. This container certainly will be modified in future ES4PS releases to add support for more operations like computers within a domain administration, more complex user operations such as custom permissions and groups, and so on. If you're willing to customize the Django web application in your ES4PS flavor, you should start by studying the `django/Dockerfile` and `django/es4c_manager/main/views.py` files.
    - `reverse-proxy`: This is the nginx container that will expose the Django web application to the end user in a secure way. Like `rabbitmq`, it is highly unlikely that you'll ever have to change anything in this service.
