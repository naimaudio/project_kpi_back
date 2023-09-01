Hours KPI Project
============================================

This project includes two git repositories:  
- https://github.com/naimaudio/projects_kpi: The present repository, with the backend and docker installation.
- https://github.com/naimaudio/project_kpi_back: The frontend repository. It should be placed in the ``./frontend`` folder.

# Application architecture

The application contains four containers:

- backend-prod: provides the API at port 8080. It parses an http request to the frontend and uses its connection with the database according to request needs.
- frontend-prod: javascript (Vue) single page application. Used by employees to manage their hours. Used by project and business managers to have a vue on there projects.
- pgadmin: not required in production.
- traefik : a reverse proxy. Provides https to port 8083 for backend-prod.

# Setup production environnement

Once the two repositories have been cloned (downloaded) in their correct paths, you can setup SSL certificates, the database, the DNS, Azure, backend, frontend and powerautomate.

### SSL Certificates

In ```./certificates``, certificates and private keys are placed for frontend and backend TLS support.

The default names are : 
- Frontend key: ```project-kpi.verventaudio.com.key```
- Frontend certificate: ```project-kpi.verventaudio.com.cer```
- Backend key: ```decrypted.project-kpi-api.verventaudio.com.key```
- Backend certificate: ```project-kpi-api.verventaudio.com.crt```

### SQL Database

This project requires the installation of a database on the host machine. This database is created in PostgreSQL v13.0, a database system that allows management of data through SQL language. For more information on PostgreSQL and databases, please refer to https://www.postgresql.org/about/. Currently, the existing database is called "project_kpi" and it is only accessible through the 'kpi' user, which is the owner of the database.

Some useful Postgres commands:

- To open postgres (only if registered as user postgres):

```bash
psql
```
- To open the database project_kpi (only if registered as user kpi):

```bash
psql -d project_kpi
```
- To backup the current base (only if registered as user postgres, when on the desired folder):

```bash
pg_dump project_kpi > {filename.sql}


- On psql, to see the connections (tables) of the current database:

```postgres
\c
```
- On psql, to see the current databases:
```postgres
\d
```
- On psql, to run a .sql file
```postgres
\i {filename}
```

A Figma ERM model was created for this project to explain the different relations and tables of the database. This model can be found on the following link:

- https://www.figma.com/file/CiYoYrg0jksPsNxgF4ehfQ/Data-Model?type=whiteboard&node-id=0%3A1&t=BdszJ0zxorvjtChA-1

In simple terms, each "user" can have several "records" associated, which on their own have a smaller unit called "record_projects", consisting of a date, user, a "project" and a number of hours worked. This number must not sum more than 35 hours per week (i.e. summing the hours of all the record_projects for a record). Users can have "favorite" projects and can make daily records instead of weekly ones; this information is stored on a buffer table called "buffer_table_register" and subsequently translated to the "record" and "record_project" tables. Projects can have "monthly_forecasts" in case users want to predict the number of worked hours before they occur; there are also "project_phases" linked to each project in case the user wants to add the effective duration of said phases through a time interval. Finally, users can modify the worked hours on a monthly basis, and these modified hours are registered in a table called "monthly_modified_hours". For more information about the interaction of these classes, please refer to the Figma schema and the README.md in the backend folder.

A backup of the current database can be found in /var/lib/pgsql/13/backups.

### pgAdmin

pgAdmin is a database tool for analysing the performance of a database in real time. To configure our pgAdmin tool, one must check that the option "network_mode" is set to "host" on the "docker-compose" file, so that the container addresses do not differ from the host address. By setting the image and the container variables, Docker will understand the container as an instance for running pgAdmin. Once there, by clicking on the option "Add new server" on the landing page, one can add the database route for pgAdmin to read. For our current database, the credentials for adding the database must be defined beforehand in the .env file in the backend folder (see the README.md file on the backend folder for more details on this route). Also, be sure to let the database listen on every address in the "postgres.conf" file (by setting listen_addresses = '*') and add the IP of the listener in the "pg_hba.conf" file on the route var/lib/pgsql/13/data. Check the pgAdmin documentation at https://www.pgadmin.org/docs/pgadmin4/development/getting_started.html for further details.

### DNS Records

This project uses 2 DNS records :
- ```project-kpi.verventaudio.com``` for frontend
- ```project-kpi-api.verventaudio.com``` for backend
Add the necessary records to the company's DNS.

### AZURE Application declaration

The frontend application uses Azure authentication with the openID connect with PKCE protocol.

In Azure, an application named 'Time Management Project' in "app registrations" was created.
In the "authentication" tab, "single-page application" platform was chosen.

The redirection URIs required for the development and development environments must be filled. 
They must have the following format: ```https:```//```host```:```port(if different than 443)```/```app```/```declare```"

In the host field, localhost is a valid option.

### Environment variables

Define the right environment variables for each environment.
For pgadmin use : In ```.env.pgadmin```, set the following variables :
- PGADMIN_DEFAULT_EMAIL
- PGADMIN_DEFAULT_PASSWORD
- PGADMIN_LISTEN_PORT

In ```./frontend/.env.local``` or ```./frontend/.env```, fill the following environment variables :
- VITE_AUTHORITY=```https://login.microsoftonline.com```/```  tenant ID  ```
The Directory (tenant) ID can be found on the application overview in Azure app registrations.
- VITE_REDIRECT_URI=```https://project-kpi.verventaudio.com/app/declare```
You can change it to ```https://localhost:8095/app/declare``` for a development instance of the frontend application. 
- VITE_CLIENT_ID: The Application (client) ID can be found on the application overview in Azure app registrations.
- VITE_FAST_API_URI=https://project-kpi-api.verventaudio.com:8083/api
- VITE_ORGANIZATIONS='FOCAL NAIM' Names of the organisations working together separated with a space.
- SSL_KEY_PATH='/certificates/project-kpi.verventaudio.com.key'
- SSL_CERT_PATH='/certificates/project-kpi.verventaudio.com.cer'
- SSL_KEY_PASSPHRASE: If your SSL key is encrypted and needs a passphrase, provide it.

In ```./backend/.env``` : 
- DATABASE_URL
- DISCOVERY_URL

### Power Automate reminder

Two chatbots have been created. They are Power Automate flows.
- Everydayreminder post a message every day to employees and directly sends them the link to enter their hours.
- Everyweekreminder post a message every week to employees and directly sends them the link to enter their hours.
In order to use them, please create or use an existing Microsoft Service account.

Inside the personal OneDrive of this account (you can log in on your internet browser with the service account), create two files one for each flow:
- /everyday.txt : In this file write all users who will be recalled every day using the daily input method 
- /everyweek.txt : In this file write all users  who will be recalled every week using the weekly input method 
The files must be as follows:
```
j.dupond@gmail.com,c.bravo@gmail.com,j.doe@outlook.com,x.lambda@orange.com
```
No backendspace or whitespace characters must be present, even at the end of the file. Once these files are ready, activate the flows.
Everydayreminder will check everyday.txt, Everyweekreminder will check everyweek.txt and notify users.

# Execution

To execute the stack :

```bash
docker compose up
```

To execute the stack in detached mode :

```bash
docker compose up -d
```

To see the realtime logs for backend you can up the container : 

```bash
docker compose up backend
```

To fetch the lastest version of the frontend, rebuild and launch again the frontend container :

```bash
./scripts/update-frontend
```

The "update-frontend" script in ```scripts/update-frontend.bash``` is used to update the frontend to the lastest version in the branch Master and launch it again.

If it doesn't work, it means that it remains eslint or there are typing errors in the frontend code (if it remains with errors, the build will not be successful).

# Ports:

## Backend

Default port : 8080

Mode : HTTPS

In ```traefik.prod.toml``` edit the line : 
```toml
  [entryPoints.websecure]
  address = ":8080"
```
Replace 8080 with the port you want and rebuild the container

## Frontend

Default port : 443

Mode : HTTPS

In ```frontend/package.json``` edit the line : 
```
    "preview": "vite preview --host --port 443",
```
Replace 443 with the port you want

## pgAdmin

Default port : 8091

Mode : HTTP

In ```.env.pgadmin``` edit the line : 
```
PGADMIN_LISTEN_PORT=8091
```
Replace 8091 with the port you want
