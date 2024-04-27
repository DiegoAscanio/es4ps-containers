#!/bin/bash

export $(cat ./.env | xargs)

docker-compose down
