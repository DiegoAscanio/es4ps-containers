#!/bin/bash

# define a bash function to generate ssl certificates for rabbit-mq

generate_rabbitmq_certificates () {
  # make a directory to store the private key
  mkdir -p /privkey-and-csr-factory/rabbitmq
  # generate a private key
  openssl genrsa -out /privkey-and-csr-factory/rabbitmq/priv.key 2048
  # generate a CA certificate
  openssl req -x509 -new -key /privkey-and-csr-factory/rabbitmq/priv.key -sha256 -out /opt/certificates/rabbitmq_cacert.pem -days 36500 -subj '/CN=My RabbitMQ CA'
  # generate server/client private key 
  openssl genrsa -out /opt/certificates/rabbitmq_serverclient_key.pem 2048
  # generate a certificate signing request
  openssl req -new -key /opt/certificates/rabbitmq_serverclient_key.pem -out /privkey-and-csr-factory/rabbitmq/serverclient_cert.csr -subj '/CN=serverclient'
  # generate server/client certificate signed by the CA
  openssl x509 -req -in /privkey-and-csr-factory/rabbitmq/serverclient_cert.csr -CA /opt/certificates/rabbitmq_cacert.pem -CAkey /privkey-and-csr-factory/rabbitmq/priv.key -CAcreateserial -out /opt/certificates/rabbitmq_serverclient_cert.pem -days 36500 -sha256
  # remove the certificate signing request
  rm /privkey-and-csr-factory/rabbitmq/serverclient_cert.csr
}

generate_nginx_certificates () {
  # make a directory to store the private key
  mkdir -p /privkey-and-csr-factory/nginx
  # generate a self signed certificate for nginx
  openssl req -x509 -nodes -days 36500 -newkey rsa:2048 -keyout /opt/certificates/nginx_server_privkey.pem -out /opt/certificates/nginx_server_fullchain.pem -config /openssl.cnf -batch
}

generate_strong_dhparam () {
  # create a strong Diffie-Hellman group
  openssl dhparam -out /opt/certificates/nginx_server_dhparam.pem 2048
}

# generate rabbitmq certificates if and only if the rabbitmq certificates do not exist
if [[ ! -f /opt/certificates/rabbitmq_cacert.pem ]] && [[ ! -f /opt/certificates/rabbitmq_serverclient_key.pem ]] && [[ ! -f /opt/certificates/rabbitmq_serverclient_cert.pem ]]; then
  generate_rabbitmq_certificates
fi

# generate nginx certificates if and only if the nginx certificates do not exist
if [[ ! -f /opt/certificates/nginx_server_fullchain.pem ]] && [[ ! -f /opt/certificates/nginx_server_privkey.pem ]] ; then
  generate_nginx_certificates
fi

# generate a strong Diffie-Hellman group if and only if the dhparam file does not exist
if [[ ! -f /opt/certificates/nginx_server_dhparam.pem ]]; then
  generate_strong_dhparam
fi

exit 0
