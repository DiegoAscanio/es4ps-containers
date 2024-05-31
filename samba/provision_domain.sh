#!/bin/bash

# provision domain only and if only it ain't provisioned yet
if [ ! -f /var/lib/samba/private/secrets.tdb ]; then

  # Provision the domain
  samba-tool domain provision --server-role=${SERVER_ROLE} --host-name=${SERVER_HOSTNAME} --dns-backend=${SERVER_DNS_BACKEND} --realm=${SERVER_REALM} --domain=${SERVER_DOMAIN} --adminpass=${SAMBA_ADMIN_PASSWORD} --use-rfc2307;

  # Backup the original samba configurations files
  cp -r /etc/samba /etc/samba.initial;
  cp -r /var/lib/samba /var/lib/samba.initial;

  # enable dns forwarder
  cat /etc/samba/smb.conf | sed 's/dns forwarder =.*/dns forwarder = 1.1.1.1/' | envsubst > /tmp/aux;
  mv /tmp/aux /etc/samba/smb.conf;

fi

# Configure Kerberos to use the Samba AD DC as the KDC
cp /var/lib/samba/private/krb5.conf /etc/krb5.conf;
