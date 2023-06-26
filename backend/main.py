from typing import Union

import os
import uvicorn
from fastapi import FastAPI , HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sqlalchemy import DBSessionMiddleware,db
from typing import List

from schemas import HoursUser as SchemaHoursUser
from schemas import Project as SchemaProject
from schemas import Register as SchemaRegister

from models import HoursUser as ModelHoursUser
from models import Project as ModelProject
from models import Register as ModelRegister


from dotenv import load_dotenv

load_dotenv(".env")

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(DBSessionMiddleware, db_url=os.environ["DATABASE_URL"])


@app.get("/")
def read_root():
    print('hrlf')
    return {"details": "Hi World"}

@app.post("/register-hours/",response_model=SchemaRegister)
def register_hours(register: SchemaRegister):
    if not project_exists(register.project_id):
        raise HTTPException(status_code=404,detail="Project not found")

    db_register = ModelRegister(
        worked_hours=register.worked_hours,
        project_id=register.project_id,
        user_id=register.user_id
    )

    db.session.add(db_register)
    db.session.commit()
    return db_register

@app.post("/new-project/",response_model=SchemaProject)
def add_project(project: SchemaProject):
    db_project = ModelProject(
        division=project.division,
        type=project.type,
        classification=project.classification,
        name=project.name,
        capitalization=project.capitalization,
        entity=project.entity
        )
    
    db.session.add(db_project)
    db.session.commit()
    return db_project

@app.post("/new-user/",response_model=SchemaHoursUser)
def add_user(hoursuser: SchemaHoursUser):
    db_user = ModelHoursUser(email=hoursuser.email,username=hoursuser.username,password=hoursuser.password)
    db.session.add(db_user)
    db.session.commit()
    return db_user

@app.get("/projects",response_model=List[SchemaProject])
def get_project():
    projects =db.session.query(ModelProject).all()
    return projects


def project_exists(project_id: Union[int,str]) -> bool:
    project = db.session.query(ModelProject).get(project_id)
    return project is not None
