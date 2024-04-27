#!/bin/bash

export $(cat ./.env | xargs)

#docker compose up -d
docker compose up
