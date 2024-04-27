#
# NOTE: THIS DOCKERFILE IS GENERATED VIA "apply-templates.sh"
#
# PLEASE DO NOT EDIT IT DIRECTLY.
#

FROM rabbitmq:3.13

# receive args from building

ARG RABBITMQ_DEFAULT_USER
ARG RABBITMQ_DEFAULT_PASS
ARG RABBITMQ_DEFAULT_VHOST

# and set these args as environment variables for the container

ENV RABBITMQ_DEFAULT_USER=${RABBITMQ_DEFAULT_USER}
ENV RABBITMQ_DEFAULT_PASS=${RABBITMQ_DEFAULT_PASS}
ENV RABBITMQ_DEFAULT_VHOST=${RABBITMQ_DEFAULT_VHOST}
ENV RABBITMQ_PID_FILE=/var/run/rabbitmq/pid

RUN set eux; \
	rabbitmq-plugins enable --offline rabbitmq_management; \
# make sure the metrics collector is re-enabled (disabled in the base image for Prometheus-style metrics by default)
	rm -f /etc/rabbitmq/conf.d/20-management_agent.disable_metrics_collector.conf; \
# grab "rabbitmqadmin" from inside the "rabbitmq_management-X.Y.Z" plugin folder
# see https://github.com/docker-library/rabbitmq/issues/207
	cp /plugins/rabbitmq_management-*/priv/www/cli/rabbitmqadmin /usr/local/bin/rabbitmqadmin; \
	[ -s /usr/local/bin/rabbitmqadmin ]; \
	chmod +x /usr/local/bin/rabbitmqadmin; \
	apt-get update; \
	apt-get install -y --no-install-recommends python3; \
	rm -rf /var/lib/apt/lists/*; \
	rabbitmqadmin --version

# Start the rabbitmq server in dettached mode to create the 
# default user, password and vhost
RUN set eux; \
    rabbitmq-server -detached; \
    rabbitmqctl wait $RABBITMQ_PID_FILE; \
    rabbitmqctl add_vhost $RABBITMQ_DEFAULT_VHOST; \
    rabbitmqctl set_user_tags $RABBITMQ_DEFAULT_USER administrator; \
    rabbitmqctl set_permissions -p $RABBITMQ_DEFAULT_VHOST $RABBITMQ_DEFAULT_USER \".*\" \".*\" \".*\"

# Copy configurations to enable ssl
COPY ./20-rabbitmq-ssl.conf /etc/rabbitmq/conf.d/20-rabbitmq-ssl.conf
COPY ./30-rabbitmq-management-https.conf /etc/rabbitmq/conf.d/30-rabbitmq-management-https.conf

# Copy wait_for_certificates.sh script to wait for the certificates to be generated
COPY ./wait_for_certificates.sh /usr/local/bin/wait_for_certificates.sh

# Create a minimum entrypoint script that will call the wait_for_certificates.sh script and then exec the CMD
RUN printf "#!/bin/bash\n\n\
set -eux\n\n\
source wait_for_certificates.sh\n\n\
exec \"\$@\"\n" > /entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /entrypoint.sh

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Expose the ports for the rabbitmq 

EXPOSE 5671 15671

# Start the rabbitmq server
CMD ["rabbitmq-server"]
