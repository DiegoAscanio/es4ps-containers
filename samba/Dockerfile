FROM --platform=linux/386 debian:latest 

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

# Verify that the /etc/hosts file on container correctly maps the hostname to the IP address
RUN printf "#!/bin/bash\n\n\
# Add entry to /etc/hosts\n\
echo '%s %s.%s %s' >> /etc/hosts\n\
# Add entry to /etc/resolv.conf\n\
echo 'search %s' > /etc/resolv.conf\n\
echo 'nameserver %s' >> /etc/resolv.conf\n\n\
# Verify if /var/lib/samba is empty (first container start)\n\
if [ -z \"\`ls -A /var/lib/samba\`\" ]; then\n\
    # Copy the initial samba files\n\
    cp -R /var/lib/samba.initial/* /var/lib/samba\n\
fi\n\n\
# Verify if /etc/samba is empty (first container start)\n\
if [ -z \"\`ls -A /etc/samba\`\" ]; then\n\
    # Copy the initial samba config files\n\
    cp -R /etc/samba.initial/* /etc/samba\n\
fi\n\n\
# Wait for certificates\n\
source /usr/local/bin/wait_for_certificates.sh\n\n\
# Start samba\n\
/usr/sbin/samba\n\n\
# Execute the main container command\n\
exec \"\$@\"\n" "${SERVER_IP}" "${SERVER_HOSTNAME}" "${SERVER_REALM}" "${SERVER_HOSTNAME}" "${SERVER_REALM}" "${SERVER_IP}" > /usr/sbin/entrypoint.sh

# Install samba and its required dependencies in non-interactive mode
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install acl attr samba winbind libpam-winbind libnss-winbind krb5-config krb5-user dnsutils python3-setproctitle python3-samba python3-pip -y

# Install celery
RUN pip3 install --break-system-packages celery

# Provision Samba AD DC in non-interactive mode
RUN rm /etc/samba/smb.conf
RUN samba-tool domain provision --server-role=${SERVER_ROLE} --host-name=${SERVER_HOSTNAME} --dns-backend=${SERVER_DNS_BACKEND} --realm=${SERVER_REALM} --domain=${SERVER_DOMAIN} --adminpass=${SERVER_ADMIN_PASSWORD} --use-rfc2307

# Set environment variables for samba and celery
ENV SAMBA_ADMIN_PASSWORD=${SERVER_ADMIN_PASSWORD}
ENV RABBITMQ_HOST=${RABBITMQ_HOST}
ENV RABBITMQ_PORT=${RABBITMQ_PORT}
ENV RABBITMQ_USER=${RABBITMQ_USER}
ENV RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
ENV RABBITMQ_VHOST=${RABBITMQ_VHOST}

# Configure Kerberos to use the Samba AD DC as the KDC
RUN cp /var/lib/samba/private/krb5.conf /etc/krb5.conf

# Backup the original samba configurations files
RUN cp -r /etc/samba /etc/samba.initial
RUN cp -r /var/lib/samba /var/lib/samba.initial

# Copy the samba user management tasks script
COPY samba_user_management /opt/celery/samba_user_management

# Make the entrypoint script executable
RUN chmod +x /usr/sbin/entrypoint.sh

# Set the entrypoint script as the main container command
ENTRYPOINT ["/usr/sbin/entrypoint.sh"]

# Start celery worker to create (and update) samba users
WORKDIR /opt/celery
CMD ["celery", "-A", "samba_user_management", "worker", "--loglevel=info"]
