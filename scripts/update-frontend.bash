#!/bin/bash
cd /home/fast
docker compose stop frontend
cd frontend
git pull origin master
cd ../
docker compose build frontend
docker compose up frontend -d
