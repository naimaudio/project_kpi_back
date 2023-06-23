from typing import Union

import os
import uvicorn
from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware,db

from schemas import HoursUser as SchemaHoursUser
from schemas import Project as SchemaProject
from schemas import Register as SchemaRegister

from models import HoursUser as ModelHoursUser
from models import Project as ModelHoursProject
from models import Register as ModelHoursRegister


from dotenv import load_dotenv

load_dotenv(".env")

app = FastAPI()

app.add_middleware(DBSessionMiddleware, db_url=os.environ["DATABASE_URL"])


@app.get("/")
def read_root():
    print('hrlf')
    return {"details": "Hi World"}

@app.post("/register-hours/",response_model=SchemaRegister)
def register_hours(register: SchemaRegister):
    db_register = ModelHoursRegister(worked_hours=register.worked_hours,project_id=register.project_id,user_id=register.user_id)
    db.session.add(db_register)
    db.session.commit()
    return db_register
