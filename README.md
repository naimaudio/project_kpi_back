
Hours KPI Project
============================================

To execute the stack :

```bash
docker compose up
```

To fetch the lastest version of the frontend, rebuild and launch again the frontend container :

```bash
./scripts/update-frontend
```


The "update-frontend" script in ```scripts/update-frontend.bash``` is used to update the frontend to the lastest version in the branch Master and launch it again.

# How to change ports

## Backend

In ```backend/Dockerfile``` edit the line : 
```
CMD ["uvicorn", "main:app", "--host", "192.168.14.30", "--port", "8080", "--reload"]
```
Replace 8080 with the port you want

## Frontend

In ```frontend/package.json``` edit the line : 
```
    "preview": "vite preview --host --port 443",
```
Replace 443 with the port you want

## Pgadmin

In ```docker-compose.yml``` edit the line : 
```
      - PGADMIN_LISTEN_PORT=8091
```
Replace 8091 with the port you want

# Docker-compose Draft :
```
  db:
    container_name: "postgresql_db"
    image: postgres
    restart: always
    ports:
      - "5433:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=hours_test
    volumes:
      - /var/lib/pgsql/data:/var/lib/pgsql/data
```