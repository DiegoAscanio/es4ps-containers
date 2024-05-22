FROM --platform=linux/386 i386/alpine:latest

# Define the following arguments needed to samba in non-interactive mode

ARG SERVER_ROLE=dc
ARG SERVER_HOSTNAME=es4cdc01
ARG SERVER_DNS_BACKEND=SAMBA_INTERNAL
ARG SERVER_IP
ARG SERVER_REALM
ARG SERVER_DOMAIN
ARG SERVER_ADMIN_PASSWORD
ARG RABBITMQ_HOST
ARG RABBITMQ_PORT=5671
ARG RABBITMQ_USER
ARG RABBITMQ_PASSWORD
ARG RABBITMQ_VHOST

# Copy wait for certificates script
COPY ./wait_for_certificates.sh /usr/local/bin/wait_for_certificates.sh
RUN chmod +x /usr/local/bin/wait_for_certificates.sh

# Copy provision domain script
COPY ./provision_domain.sh /usr/local/sbin/provision_domain.sh
RUN chmod +x /usr/local/sbin/provision_domain.sh

# Verify that the /etc/hosts file on container correctly maps the hostname to the IP address
RUN printf "#!/bin/bash\n\n\
# Add entry to /etc/hosts\n\
echo '%s %s.%s %s' >> /etc/hosts\n\
# Add entry to /etc/resolv.conf\n\
echo 'search %s' > /etc/resolv.conf\n\
echo 'nameserver %s' >> /etc/resolv.conf\n\n\
# Wait for certificates\n\
source /usr/local/bin/wait_for_certificates.sh\n\n\
# Provision the domain\n\
source /usr/local/sbin/provision_domain.sh\n\n\
# Start samba\n\
/usr/sbin/samba\n\n\
# Execute the main container command\n\
exec \"\$@\"\n" "${SERVER_IP}" "${SERVER_HOSTNAME}" "${SERVER_REALM}" "${SERVER_HOSTNAME}" "${SERVER_REALM}" "${SERVER_IP}" > /entrypoint.sh

# Add pin to the alpine edge repository
RUN echo "@edge https://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories

# Install chrony from the alpine edge repository
RUN apk update && \
    apk add --no-cache chrony@edge chrony-doc@edge

# Install samba and its required dependencies in non-interactive mode
RUN apk update && \
    apk add --no-cache acl attr samba-dc samba-winbind pam-winbind samba-libnss-winbind krb5 krb5-dev bind-tools py3-setproctitle py3-samba python3 py3-pip bash envsubst

# Install celery
RUN pip install --break-system-packages celery

# Set environment variables for samba and celery
ENV SAMBA_ADMIN_PASSWORD=${SERVER_ADMIN_PASSWORD}
ENV SERVER_ROLE=${SERVER_ROLE}
ENV SERVER_HOSTNAME=${SERVER_HOSTNAME}
ENV SERVER_DNS_BACKEND=${SERVER_DNS_BACKEND}
ENV SERVER_REALM=${SERVER_REALM}
ENV SERVER_DOMAIN=${SERVER_DOMAIN}
ENV SERVER_IP=${SERVER_IP}

ENV RABBITMQ_HOST=${RABBITMQ_HOST}
ENV RABBITMQ_PORT=${RABBITMQ_PORT}
ENV RABBITMQ_USER=${RABBITMQ_USER}
ENV RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
ENV RABBITMQ_VHOST=${RABBITMQ_VHOST}

# Copy the samba user management tasks script
COPY samba_user_management /opt/celery/samba_user_management

# Make the entrypoint script executable
RUN chmod +x /entrypoint.sh

# Set the entrypoint script as the main container command
ENTRYPOINT ["/entrypoint.sh"]

# Start celery worker to create (and update) samba users
WORKDIR /opt/celery
CMD ["celery", "-A", "samba_user_management", "worker", "--loglevel=info"]
