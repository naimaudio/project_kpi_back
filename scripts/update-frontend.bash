#!/bin/bash
cd /home/fast
VAR=$(docker ps -aqf "name=frontend")
docker compose stop frontend
docker rm $VAR
cd frontend
git pull origin master
cd ../
docker compose build frontend
docker compose up frontend -d
