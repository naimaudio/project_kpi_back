
Hours KPI Project
============================================

This project includes two git repositories:  
- https://github.com/naimaudio/projects_kpi: The present repository, with the backend and docker installation.
- https://github.com/naimaudio/project_kpi_back: The frontend repository. It should be placed in the ``./frontend`` folder.

# Setup production environnement

Clone 
Once the 2 repositories have been cloned (downloaded).

### SSL Certificates

In ``./certificates`` : 
- Place certificates and private keys for frontend and backend TLS support.
The default names are : 
- Frontend key: project-kpi.verventaudio.com.key
- Frontend certificate: project-kpi.verventaudio.com.cer 
- Backend key: decrypted.project-kpi-api.verventaudio.com.key
- Backend certificate: project-kpi-api.verventaudio.com.crt

### SQL Database

This project requires the installation of a blank psql database on the host machine.

### DNS Records

This project uses 2 DNS records :
- project-kpi.verventaudio.com pour le frontend
- project-kpi-api.verventaudio.com pour le backend
Add the necessary records to the company's DNS.

### AZURE Application declaration

The frontend application uses Azure authentication with the openID connect with PKCE protocol.
In Azure,
Create an application in "app registrations". You can name it 'Time Management Project'.
In its "authentication" tab, add a "single-page application" platform.
Fill in the redirection URIs required for the development and development environments".
The rediction URI must be as followed : "https://<<host>>:<<port if different than 443>>/app/declare"
localhost works.


### Powerautomate reminder

Two chatbots have been created. They are powerautomate flows.
- Everydayreminder post a message every day to employees and directly send them the link to enter their hours.
- Everyweekreminder post a message every week to employees and directly send them the link to enter their hours.
In order to use them, please create or use an existing microsoft service account.
Then inside the personnal onedrive of this account, (you can log in on your internet browser with the service account), create two files one for each flow :
- /everyday.txt : In this file write all users who will be recalled every day using the daily input method 
- /everyweek.txt : In this file write all users  who will be recalled every week using the weekly input method 
The files must be as followed :
```
j.dupond@gmail.com,c.bravo@gmail.com,j.doe@outlook.com,x.lambda@orange.com
```
It must be without backendspace, whitepaces characters even at the end of the file.

Then activate the flows.
Everydayreminder will check everyday.txt, Everyweekreminder will check everyweek.txt and notify users.

## Environment variables

Define the correct environment variables for each environment.
For pgadmin use : In ```.env.pgadmin```, set the following variables :
- PGADMIN_DEFAULT_EMAIL
- PGADMIN_DEFAULT_PASSWORD
- PGADMIN_LISTEN_PORT

In ```./frontend/.env.local``` or ```./frontend/.env``` : fill the following environment variables :
- VITE_AUTHORITY=https://login.microsoftonline.com/<<tenant ID>>
The Directory (tenant) ID can be found on the application overview in azure app registrations.
- VITE_REDIRECT_URI=https://project-kpi.verventaudio.com/app/declare
Change to https://localhost:8095/app/declare for instance for a developpement instance of frontend application 
- VITE_CLIENT_ID=<<client ID>> 
The Application (client) ID can be found on the application overview in azure app registrations.
- VITE_FAST_API_URI=https://project-kpi-api.verventaudio.com:8083/api
- VITE_ORGANIZATIONS='FOCAL NAIM' 
- SSL_KEY_PATH='/certificates/project-kpi.verventaudio.com.key'
- SSL_CERT_PATH='/certificates/project-kpi.verventaudio.com.cer'
- SSL_KEY_PASSPHRASE if necessary

In ```./backend/.env``` : 
- DATABASE_URL
- DISCOVERY_URL

# Execution

```bash
docker compose up
```
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

If it doesn't work, it means that it remains eslint or type errors in frontend code. (if it remains errors the build will not be successfull)

# How to change ports

## Backend

In ```backend/Dockerfile``` edit the line : 
```
CMD ["uvicorn", "main:app", "--host", "192.168.14.30", "--port", "8080", "--reload"]
```
Replace 8080 with the port you want and rebuild the container

## Frontend

In ```frontend/package.json``` edit the line : 
```
    "preview": "vite preview --host --port 443",
```
Replace 443 with the port you want

## Pgadmin

In ```.env.pgadmin``` edit the line : 
```
PGADMIN_LISTEN_PORT=8091
```
Replace 8091 with the port you want
