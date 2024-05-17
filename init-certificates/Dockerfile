FROM --platform=linux/386 i386/alpine:latest

# Set ARGS

ARG HOST_FQDN

# Set environment variables from ARGS
ENV HOST_FQDN=${HOST_FQDN}

# Upgrade the system and install required packages
RUN apk update && apk add --no-cache openssl gettext bash envsubst

# Copy openssl.cnf.template to the container
COPY openssl.cnf.template /

# Perform variable substitution in openssl.cnf.template
RUN envsubst < /openssl.cnf.template > /openssl.cnf

# Copy generate-certificates.sh to the container
COPY generate-certificates.sh /generate-certificates.sh
RUN chmod +x /generate-certificates.sh

# Run the script
CMD ["/generate-certificates.sh"]
