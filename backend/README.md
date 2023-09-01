# Backend Documentation
    Version 0.0

The purpose of this backend application is to grant access to the database that contains information about the working time of FOCAL employees in their respective projects, along with all the paths and routes for the information to be accessible to users in a frontend inteface according to their role.

## Concept and backend explanation

### FastAPI and its modules

For handling the database within FastAPI, we use two main libraries: SQLAlchemy and Pydantic.

#### SQLAlchemy

FastAPI does not recognize SQL language. SQLAlchemy works as a translator between SQL and Python by using a tool called Object Relational Mapping (ORM) which basically transforms SQL tables into objects and table columns into attributes. An easy example would be a table of users made of two columns: user name and email. By using ORM, SQLAlchemy would access the table by creating a object called User and adding two attributes: name and email. If you wanted to retrieve all your users' names, you could access them in Python by using "User.name()" and SQLAlchemy would translate that query to SQL language, receive the result and then send it back to your application. For the current project, we mapped the database structure we had into the "models.py" file, ensuring the relations were kept and granting access to the database by defining the address in the ".env" file. For further assistance respecting SQLAlchemy implementation, refer to https://docs.sqlalchemy.org/en/20/.

#### Pydantic

The communication between the PostgreSQL and FastAPI has been set, but there is not yet a fluid channel for communicating with the information received from the frontend. Pydantic allows to create schemas, which are models that fit into the SQLAlchemy models for receiving and sending information from the frontend. Overall, the main goal of the pydantic schemas is to ensure that the information is received correctly. There is no need to include relationships between variables, but the types must be consistent with the already created SQLAlchemy models. In this particular project, the Pydantic models were defined on the file "schemas.py". For more information, please refer to https://docs.pydantic.dev/latest/usage/models/.

### Method main

Following on the profile structure set for the project, methods are divided according to the profile that has access to them. Employee methods are marked as 1, Project Manager methods as 2 and Business Manager methods as 3. For each type of entity, CRUD (Create, Read, Update, Delete) methods are created in the "main.py" file, which specifies the link between the Pydantic schemas and the SQLAlchemy models. This is done by creating HTTP methods such as GET, PUT, PATCH, POST and DELETE and by associating input information from the frontend (in the form of a schema) to the database information, according to the needs. All endpoints start with "/api" to differentiate them from other routes. Methods altering the same entity have the same endpoint route for easier implementation (e.g. the POST and GET methods for the user entity are both '/api/user'). Most information sent or received to/from the frontend is in JSON format.

#### 1. Employees

Employees must have rights for registering hours, observing project features, modifying their own records and tracking their inputted hours. Also, their profile requires the database to show their personal information. These functions are represented by the methods:

* 1.1. Get user: uses the authentication token to retrieve the user email and searches its features in the database.

* 1.2. Get user ID: exactly the same as get user, but specific for finding the ID.

* 1.3. Insert record: verifies the user, creates a record with the inputted information and then creates the record projects associated to that record. Also validates that the total hours are exactly 35 within one week.

* 1.4. Get record: shows the record projects associated to the current user.

* 1.5. Modify hours in records: allows for users to change their records if they want to. Frontend validates this is only available for weeks that are yet to pass.

* 1.6. Get projects: shows the list of all projects.

* 1.7. Define favorites: allows users to register their favorite projects.

* 1.8. Get favorites: shows the favorite projects of the current user.

* 1.9. Delete favorites: erases a specific favorite project for the current user.

* 1.10. Get user domain: shows the domain for the current user.

* 1.11. Update user domain: allows to change the domain of the current user. Frontend validates this method is available only once in a month.

* 1.12. Input to buffer table: allows user to register hours per day in a buffer table created for such end.

* 1.13. Get buffer table records: shows the buffer table register for the current user.

#### 2. Project Managers

Aside from their regular employee functions, project managers must also be able to observe relevant KPIs to their projects, see the records set by employees and change project features to their will. These functions are thus represented by the following methods:

* 2.1. Export records CSV: creates a CSV file, registers in it every record project set within the provided dates (or the whole time horizon if dates are not given) and downloads it locally. 

* 2.2. Import records CSV: recieves a CSV file in the same format as the export and modifies the records in the database accordingly.

* 2.3. Add project: adds a new project with all its features, but also with the additional classes linked to it (phases and forecasts) in case they are provided.

* 2.4. Get project: shows the project features and its associated classes.

* 2.5. Modify project: modifies the project features and/or their associated classes, if provided information.
 
* 2.6. Delete project: deletes the project associated classes and then proceeds to delete the project with its features.

* 2.7. KPI pie chart: gathers information from the dates (optional) and the inputted project and shows the distribution of hours per domain in a pie chart. Also has an option for changing units between hours and TDE.

* 2.8. KPI line graph: gathers information from the dates (optional) and the inputted project and shows the distribution of hours per date in a line chart. Additionally, shows the forecast for the project in the same time horizon for easy comparison. Also has an option for changing units between hours and TDE, and another option for showing accumulated info vs monthly info. 

* 2.9. KPI stacked bar chart: gathers information from the dates (optional) and the inputted project and shows the distribution of hours per phase in a stacked bar chart. Also has an option for changing units between hours and TDE, and another option for showing accumulated info vs monthly info.

* 2.10. See data: gathers the inputted records for the specified projects (optional, will show all projects if not chosen) and the specified dates (optional, will show all time horizon if not chosen) and shows them.

#### 3. Business Managers

While able to use their Employee and Project Manager features, business managers should be able to do two additional functions: see and alter records from a monthly basis, and obtain specific business KPIs that reflect these changes. These are performed within the following methods:

* 3.1. Get monthly hours: obtain the monthly modified hours for a given month.

* 3.2. Modify monthly hours: change the monthly modified hours for a given month and specific combinations of users and projects.

* 3.3. Reset monthly hours: resets the whole monthly modified hours for a given month to the default: the sum of the declared hours for the weeks of that month. The assumed convention says that if 3 days out of 5 are within a current month, the week is counted for that month.

* 3.4. Business KPIs, capitalization summary pie: gathers information from the dates (optional) and the inputted project and shows the distribution of monthly modified hours per division and capitalization status in a nested pie chart that also includes the net capitalized and not capitalized hours. Also has an option for changing units between hours and TDE. Start and end dates can be the same to show the information for a specific month.

* 3.5. Business KPIs, capitalization summary bar: gathers information from the dates (optional) and the inputted project and shows the distribution of hours per phase in a stacked bar chart. Also has an option for changing units between hours and TDE, and another option for showing accumulated info vs monthly info. Start and end dates can be the same to show the information for a specific month.

* 3.6. Business KPIs, stacked non-cap line: gathers information from the dates (optional) and the inputted project and shows the evolution of the non-capitalized hours and Eng. change/prod support within the time horizon. Also has an option for changing units between hours and TDE.

* 3.7. Business KPIs, line: gathers information from the dates (optional) and the inputted project and shows the distribution of modified monthly hours per date in a line chart. Also has an option for changing units between hours and TDE, and another option for showing accumulated info vs monthly info. 

* 3.8. Business KPIs, pie: gathers information from the dates (optional) and the inputted project and shows the distribution of monthly modified hours per domain in a pie chart. Also has an option for changing units between hours and TDE.

* 3.9. Get users: shows all users. Required for the monthly report table.

* 3.10. Export monthly hours: creates a CSV file, registers in it every modified monthly hours record set within the provided dates (or the whole time horizon if dates are not given) and downloads it locally. 

* 3.11. Export project capitalization summary: creates an Excel file, gives it a template format specified by FOCAL Business Managers and proceeds to fill it with the information within the database for a given month.