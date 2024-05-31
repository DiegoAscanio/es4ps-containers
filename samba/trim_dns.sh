#!/bin/bash
keep_addresses="127.0.0.1 ${SERVER_IP}"
addresses=$(echo $(echo "$(ip a sh)" | grep "inet " | sed "s/    //g" | cut -d ' ' -f2 | sed "s/\/[0-9]\{1,\}//g"))
for address in addresses; do
  if [[ -z $(echo $keep_addresses | grep $address) ]]; then
    samba-tool dns delete localhost dom.es4all.ascanio.dev @ A ${address} -U administrator%${SAMBA_ADMIN_PASSWORD};
  fi
done
