FROM --platform=linux/386 i386/alpine:latest 

# Set ARGS

ARG ES4C_MANAGER_ALLOWED_EMAIL_DOMAINS
ARG ES4C_MANAGER_SMTP_SERVER
ARG ES4C_MANAGER_SMTP_PORT
ARG ES4C_MANAGER_SMTP_USERNAME
ARG ES4C_MANAGER_SMTP_PASSWORD
ARG ES4C_MANAGER_HOST_FQDN
ARG ES4C_MANAGER_CELERY_BROKER_URL
ARG ES4C_MANAGER_CELERY_RESULT_BACKEND
ARG SAMBA_ADMIN_PASSWORD
ARG DJANGO_SUPERUSER_USERNAME
ARG DJANGO_SUPERUSER_EMAIL
ARG DJANGO_SUPERUSER_PASSWORD
ARG DJANGO_SECRET_KEY

# Set environment variables from ARGS
ENV ES4C_MANAGER_ALLOWED_EMAIL_DOMAINS=${ES4C_MANAGER_ALLOWED_EMAIL_DOMAINS}
ENV ES4C_MANAGER_SMTP_SERVER=${ES4C_MANAGER_SMTP_SERVER}
ENV ES4C_MANAGER_SMTP_PORT=${ES4C_MANAGER_SMTP_PORT}
ENV ES4C_MANAGER_SMTP_USERNAME=${ES4C_MANAGER_SMTP_USERNAME}
ENV ES4C_MANAGER_SMTP_PASSWORD=${ES4C_MANAGER_SMTP_PASSWORD}
ENV ES4C_MANAGER_HOST_FQDN=${ES4C_MANAGER_HOST_FQDN}
ENV ES4C_MANAGER_CELERY_BROKER_URL=${ES4C_MANAGER_CELERY_BROKER_URL}
ENV ES4C_MANAGER_CELERY_RESULT_BACKEND=${ES4C_MANAGER_CELERY_RESULT_BACKEND}
ENV SAMBA_ADMIN_PASSWORD=${SAMBA_ADMIN_PASSWORD}
ENV DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME}
ENV DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}
ENV DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

# Install dependencies
RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    py3-samba \
    curl \
    bash
# Curl the requirements file from github repo into /django-requirements.txt file
RUN curl -L https://raw.githubusercontent.com/DiegoAscanio/es4ps-containers/main/django/es4c_manager/requirements.txt -o /django-requirements.txt

# Install the dependencies
RUN pip install --break-system-packages -r /django-requirements.txt

# Copy wait for certificate script
COPY ./wait_for_certificates.sh /wait_for_certificates.sh
RUN chmod +x /wait_for_certificates.sh

RUN printf "#!/bin/bash\n\n\
# if there's no database make migrations, migrate, and create superuser\n\
if [[ ! -f db.sqlite3 ]]; then\n\
    if [[ -d /es4c_manager/main/migrations ]]; then\n\
        rm -rf /es4c_manager/main/migrations;\n\
    fi\n\
    if [[ -d /es4c_manager/es4c_manager/__pycache__ ]]; then\n\
        rm -rf /es4c_manager/es4c_manager/__pycache__;\n\
    fi\n\
    if [[ -d /es4c_manager/main/__pycache__ ]]; then\n\
        rm -rf /es4c_manager/main/__pycache__;\n\
    fi\n\
    python3 manage.py makemigrations;\n\
    python3 manage.py makemigrations main;\n\
    python3 manage.py migrate;\n\
    python3 manage.py createsuperuser --noinput --first_name=%s --last_name=%s;\n\
fi\n\n\
# wait for certificates\n\
source /wait_for_certificates.sh;\n\n\
# collect static files\n\
python3 manage.py collectstatic;\n\
# run the server\n\
python3 manage.py runserver 0.0.0.0:8000" $DJANGO_SUPERUSER_USERNAME $DJANGO_SUPERUSER_USERNAME > /entrypoint.sh

RUN cat /entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /entrypoint.sh

# Expose the port
EXPOSE 8000

# Set the working directory
WORKDIR /es4c_manager

# Run the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
