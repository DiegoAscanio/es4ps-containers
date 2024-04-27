#!/bin/bash

# Define the paths to the certificate files

cacert=/opt/certificates/rabbitmq_cacert.pem
server_cert=/opt/certificates/rabbitmq_serverclient_cert.pem
server_key=/opt/certificates/rabbitmq_serverclient_key.pem

# Function to check if all certificate files exist
check_certificates() {
  [[ -f "$cacert" && -f "$server_cert" && -f "$server_key" ]]
}

# Wait for all certificate files to be present
while ! check_certificates; do
  echo "Waiting for certificate files to be available..."
  sleep 1  # wait for 1 second before checking again
done

echo "All certificate files are present. Services can start now"
