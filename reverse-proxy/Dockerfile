FROM --platform=linux/386 nginx:alpine

# Set ARGS
ARG HOST_FQDN

# Set environment variables
ENV HOST_FQDN=${HOST_FQDN}
ENV DOLLAR="\$"

# Copy the nginx configuration file template
COPY nginx.conf.template /etc/nginx/nginx.conf.template

# Install bash and envsubst
RUN apk update && apk add --no-cache bash envsubst

# Create an entrypoint script to replace environment variables in the nginx configuration file
RUN printf "#!/bin/bash\n\n\
envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf\n\
source /wait_for_certificates.sh\n\
exec \"\${@}\"\n\
" > /docker-entrypoint.sh

# Make the script executable
RUN chmod +x /docker-entrypoint.sh

# Copy wait for certificates script
COPY wait_for_certificates.sh /wait_for_certificates.sh

# Make the script executable
RUN chmod +x /wait_for_certificates.sh

# EXPOSE PORTS
EXPOSE 80 443

# Run the entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]

# define stop signal
STOPSIGNAL SIGQUIT

# Start the nginx server
CMD ["nginx", "-g", "daemon off;"]
