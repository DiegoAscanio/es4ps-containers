FROM ubuntu:22.04

# Set ARGS

ARG HOST_FQDN

# Set environment variables from ARGS
ENV HOST_FQDN=${HOST_FQDN}

# Upgrade the system and install openssl
RUN apt-get update && apt-get upgrade -y && apt-get install -y openssl gettext-base

# Copy openssl.cnf.template to the container
COPY openssl.cnf.template /

# Perform variable substitution in openssl.cnf.template
RUN envsubst < /openssl.cnf.template > /openssl.cnf

# Copy generate-certificates.sh to the container
COPY generate-certificates.sh /generate-certificates.sh

# Run the script
CMD ["/generate-certificates.sh"]
