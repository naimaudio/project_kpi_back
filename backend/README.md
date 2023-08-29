# Backend Documentation
    Version 0.0

The purpose of this backend application is to generate a database that contains information about the working time of FOCAL employees in their respective projects, along with all the paths and routes for the information to be accessible to users in a frontend inteface according to their role.

## Concept and database definition

FOCAL requires to monitor the amount of hours worked in each of their projects. To this end, a website application is created with three main features:

- Input of working hours with a given frequency (mostly weekly but can be daily as well) for Employee, Project Manager and Business Manager roles
- Key Performance Indicators for Project Manager and Business Manager roles
- Alter of inputted hours (weekly for Project Manager and monthly for Business Manager)

For managing this data, a database called "project_kpi" is then created with the following tables:

* Hours User (_hoursuser_): a table containing the information of every user in the FOCAL roster. Column fields include:
    + Id (_id_): unique id for identifying each user
    + User name (_username_): complete name of every user
    + Email (_email_): corporate email for each user
    + Domain (_domain_): dependency on which each user works. Possible domains include: Mechanics, Hardware, Software, Acoutics, Tests and Project Management.
    + Role (_role_): profile for the current user. Possible profiles include: Employee, Project Manager and Business Manager.
    + View (_view_): the current view for inputting hours (daily or weekly)

* Project (_project_): contains every project FOCAL is interested in tracking. Column fields include:
    + Id (_id_): unique id for identifying each project
    + Entity (_username_): complete name of every user
    + Division (_email_): corporate email for each user
    + Sub-category (_domain_): dependency on which each user works. Possible domains include: Mechanics, Hardware, Software, Acoutics, Tests and Project Management.
    + Classification (_role_): profile for the current user. Possible profiles include: Employee, Project Manager and Business Manager.
    + Type (_view_): the current view for inputting hours (daily or weekly)
    + Project name
    + Project code
    + Project manager
    + Complexity
    + Start capitalization date:
    + End capitalization date:
    + Start date:
    + End date:

* Favorites (_favorites_): a table containing the favorite projects for each user. Column fields include:
    ...

* Declared records (_declaredrecord_): each hour input record for all projects and users. Column fields include:
    ...

* Modified records (_modifiedrecord_): contains the same information as declared records, but with updated modified hour records by the Business Manager. Column fields include:
    ...

This database is created in PostgreSQL v13.0, a database system that allows management of data through SQL language. For more information on PostgreSQL and databases, please refer to https://www.postgresql.org/about/. The database "project_kpi" is populated by executing the files included on /home/kpi/SQL_DB, each of which includes the SQL commands for creating a different table on the database (except for records.sql, which is used to populate the _hoursuser_ and _project_ tables).

## FastAPI, Docker and pgAdmin

The database is hosted locally in the current server. For performing CRUD (Create, Read, Update, Delete) operations with the database in the frontend, we use the web framework __FastAPI__, which allows to create APIs (Application Programming Interfaces) to connect the frontend with the backend. For more information on what is FastAPI and how to use it, please refer to https://fastapi.tiangolo.com/tutorial/. Several Python packages are required to effectively run FastAPI (we will later go into these details). For this reason, a Docker environment is created to host two main backend services: the FastAPI app and pgAdmin, which is an interface for managing the database. 

### Docker configuration

Docker is a platform that allows to run applications in isolated environments known as containers. Two files define the configuration of docker containers: Dockerfile and docker-compose. In the current backend Dockerfile, we define access to Python 3.9 as well as importing the packages included on the requirements.txt file. We also define the port we want to map for the backend app and the IP address. The docker-compose is an unique file for the whole configuration, meaning that it includes a frontend part that is not addressed here. For details, please check the README.md on the _frontend_ folder. This file defines what we call services, which are the three main containers: the frontend, the FastAPI app and the pgAdmin. For relevant commands and more information on Docker, please check the Docker documentation at https://docs.docker.com/get-started/overview/.

### pgAdmin

pgAdmin is a database tool for analysing the performance of a database in real time. To configure our pgAdmin tool, one must check that the option "network_mode" is set to "host", so that the container addresses do not differ from the host address. By setting the image and the container variables, Docker will understand the container as an instance for running pgAdmin. Once there, by clicking on the option "Add new server" on the landing page, one can add the database route for pgAdmin to read. For our current database, the credentials of both the server user and the PostgreSQL user match, so that there are no problems when it comes to authentication in pgAdmin. Check the pgAdmin documentation at https://www.pgadmin.org/docs/pgadmin4/development/getting_started.html for further details.

### FastAPI and its modules

Once the container is created **I haven't referenced volumes** and the mapping of the volume made for the backend folder on the host, all the python files at the volume location will affect the FastAPI application. For handling the database within the FastAPI, we use two main libraries: SQLAlchemy and Pydantic.

#### SQLAlchemy

In PostgreSQL, if you wanted to retrieve a table, you would input the following query in SQL language: "SELECT * from table_name", where "table_name" is the name of your table. This query cannot be performed in FastAPI, because it does not recognize SQL language. SQLAlchemy works as a translator between SQL and Python by using a tool called Object Relational Mapping (ORM) which basically transforms SQL tables into object and table columns into attributes. An easy example would be a table of users made of two columns: user name and email. By using ORM, SQLAlchemy would access the table by creating a objetc called User and adding two attributes: name and email. If you wanted to retrieve all your users' names, you could access them in Python by using "User.name()" and SQLAlchemy would translate that query to SQL language, recieve the result and then send it back to your application. For the current project, we mapped the database structure we had into the "models.py" file, ensuring the relations were kept and granting access to the database by defining the address in the ".env" file. For further assistance respecting SQLAlchemy implementation, refer to https://docs.sqlalchemy.org/en/20/.

#### Pydantic

The communication between the PostgreSQL and FastAPI has been set, but there is not yet a fluid channel for communicating with the information received from the frontend. Pydantic allows to create schemas, which are models that fit into the SQLAlchemy models for receiving and sending information from the frontend. Overall, the main goal of the pydantic schemas is to ensure that the information is received correctly. There is no need to include relationships between variables, but the types must be consistent with the already created SQLAlchemy models. In this particular project, the Pydantic models were defined on the file "schemas.py". For more information, please refer to https://docs.pydantic.dev/latest/usage/models/.

#### Method main

These two features are conjugated within the CRUD (Create, Read, Update, Delete) methods created in the "main.py" file, which specifies the link between the Pydantic schemas and the SQLAlchemy models. This is done by creating HTTP methods such as GET, PUT, PATCH, POST and DELETE and by associating input information from the frontend (in the form of a schema) to the database information, according to the needs. In this project, we have entities for users (_hoursusers_), projects, records (both declared and modified) and favorites **This will later change when the data model is bigger so be sure to check it out before the final version**, each of which has its own GET method and POST method (except for users which are already linked to Active Directory **Not yet done so come back later and comment about this**). There are also PUT methods for the _hoursusers_ column _domain_, so that users may change their domain if required. 


















open the python environment

source fastapi/bin/activate