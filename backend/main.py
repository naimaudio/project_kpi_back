from typing import Union, Annotated
import json
import base64
import os
import uvicorn
from fastapi import Depends, FastAPI , HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sqlalchemy import DBSessionMiddleware,db
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func
from typing import List
import datetime
from datetime import date
import csv
import aiofiles


from schemas import HoursUserBase as SchemaHoursUserBase
from schemas import HoursUser as SchemaHoursUser
from schemas import BufferDailyRegister as SchemaBufferDailyRegister
from schemas import FrontEndUser as SchemaFrontEndUser
from schemas import Project as SchemaProject
from schemas import Record as SchemaRecord
from schemas import RecordProjects as SchemaRecordProjects
from schemas import Favorites as SchemaFavorites

from models import HoursUser as ModelHoursUser
from models import Project as ModelProject
from models import Record as ModelRecord
from models import RecordProjects as ModelRecordProjects
from models import Favorites as ModelFavorites
from models import BufferDailyRegister as ModelBufferDailyRegister

from database import SessionLocal
from dotenv import load_dotenv
load_dotenv(".env")


app = FastAPI()

#OAuthScheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _b64_decode(data):
    data += '=' * (4 - len(data) % 4)
    return base64.b64decode(data).decode('utf-8')

def jwt_payload_decode(jwt):
    _, payload, _ = jwt.split('.')
    return json.loads(_b64_decode(payload))

def jwt_header_decode(jwt):
    header, _, _ = jwt.split('.')
    return json.loads(_b64_decode(header))

# Middlewares
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(DBSessionMiddleware, db_url=os.environ["DATABASE_URL"])


# Authentication Middleware
async def get_user (token: str = Depends(oauth2_scheme)):
    try:
        decoded_token= jwt_payload_decode(token)
        username = decoded_token['name']
        email = decoded_token['unique_name']
    
        user=db.session.query(ModelHoursUser).filter(ModelHoursUser.username  == username,
                                                     ModelHoursUser.email  == email).first()

        return SchemaHoursUserBase(username=user.username,
                               email = user.email)
    except Exception as e :
        return {'details':'Invalid token'}
        raise e

#Root message
@app.get("/")
def read_root():
    return {"status": "OK"}


# PART 1: METHODS FOR THE EMPLOYEE PROFILE
#____________________________________________________________________________________________________

# 1.1 Get user **
@app.get("/user")
async def get_hours_user(user: SchemaHoursUserBase = Depends(get_user)):
    
    if not user:
            raise HTTPException(status_code=400, detail="User not found")
    
    model_user=db.session.query(ModelHoursUser).filter(ModelHoursUser.username  == user.username,
                                                     ModelHoursUser.email  == user.email).first()

    frontenduser = SchemaFrontEndUser(
        email=model_user.email,
        username=model_user.username,
        id=model_user.id,  
        domain=model_user.domain,
        role=model_user.role,
        view=model_user.view,
        date_entrance=model_user.date_entrance)

    return frontenduser

# 1.2 Get user ID **
@app.get("/userID")
async def get_user_ID(user: SchemaHoursUserBase = Depends(get_user)):
    
    if not user:
            raise HTTPException(status_code=400, detail="User not found")
    
    usermodel=db.session.query(ModelHoursUser).filter(ModelHoursUser.email  == user.email).first()
    
    return str(usermodel.id)


# 1.3 Insert record **
@app.post("/records")
async def insert_record(record: SchemaRecord, projects: List[SchemaRecordProjects], user: SchemaHoursUserBase = Depends(get_user)):
    
    userID = await get_user_ID(user)

    #Before everything: verify the user
    if not str(record.user_id) == userID:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    
    if record.date_rec.weekday() != 4:
            raise HTTPException(status_code=400,detail="Invalid date")

    #First part: defining class record
    if not db.session.query(ModelHoursUser).filter(ModelHoursUser.id == record.user_id).first():
            raise HTTPException(status_code=400, detail="User not found")
        
    existing_record = db.session.query(ModelRecord).filter(
        ModelRecord.user_id == record.user_id,
        ModelRecord.date_rec == record.date_rec).first()
           
    if existing_record:
        raise HTTPException(status_code=409, detail="Record already exists")

    db_record = ModelRecord(
            user_id = record.user_id,
            comment = record.comment,
            date_rec = record.date_rec
        )
    
    #Second part: adding the project to the created record
    db_projects = []
    hourcount = 0
    
    for project in projects:
      
        if not project_exists(project.project_id):
            raise HTTPException(status_code=404,detail="Project not found")
        
        existing_project = db.session.query(ModelRecordProjects).filter(
            ModelRecordProjects.user_id == record.user_id,
            ModelRecordProjects.date_rec == record.date_rec,
            ModelRecordProjects.project_id == project.project_id
        ).first()

        if existing_project:
            raise HTTPException(status_code=409, detail="User has already filled hours for this project in this week")

        if not project.declared_hours == 0:
            db_project = ModelRecordProjects(
                user_id = record.user_id,
                date_rec = record.date_rec,
                project_id = project.project_id,
                declared_hours = project.declared_hours,
                modified_hours = project.declared_hours
            )
            db_projects.append(db_project)
        
        hourcount = hourcount + project.declared_hours
   
    if hourcount != 35:
            raise HTTPException(status_code=400,detail="Hour count does not match required value")
    
    date_init = record.date_rec - datetime.timedelta(days=4)

    searched_records = db.session.query(ModelBufferDailyRegister).filter(
        ModelBufferDailyRegister.user_id == record.user_id,
        ModelBufferDailyRegister.day_date.between(date_init, record.date_rec)
        ).all()
    
    for buffer_record in searched_records:
        db.session.delete(buffer_record)
 
    db.session.add_all(db_projects)
    db.session.add(db_record)
    db.session.commit()
    return {"message": "Record created successfully."}


# 1.4 Get record **
@app.get("/records/{hours_user_id}")
async def get_records(hours_user_id: int, user: SchemaHoursUserBase = Depends(get_user)):
    
    ans = []

    if not db.session.query(ModelHoursUser).filter(ModelHoursUser.id == hours_user_id).first():
        raise HTTPException(status_code=400, detail="User not found")
    
    userID = await get_user_ID(user)
    
    if not str(hours_user_id) == userID:
        raise HTTPException(status_code=401, detail="Unauthorized access")

    user_declaredrecords = db.session.query(ModelRecord).filter(
        ModelRecord.user_id == hours_user_id).all()
    
    for record in user_declaredrecords:
        rec_projects = []

        record_projects = db.session.query(ModelRecordProjects).filter(ModelRecordProjects.user_id == hours_user_id,
                                                                       ModelRecordProjects.date_rec == record.date_rec).all()

        for project in record_projects:
            rec_proj = SchemaRecordProjects(
                project_id= project.project_id,
                declared_hours= project.declared_hours
            )
            rec_projects.append(rec_proj)
        
        rec_ans = {"record": record,
                   "projects":rec_projects}
        ans.append(rec_ans)     

    return ans



# 1.5 Get projects**
@app.get("/projects",response_model=List[SchemaProject])
async def get_projects(user = Depends(get_user)):
    projects =db.session.query(ModelProject).all()
    if not projects:
            raise HTTPException(status_code=404,detail="No projects on database")
    return projects

# 1.6 Define favorites
@app.post("/favorites",response_model=List[SchemaFavorites])
async def define_favorites(favorites: List[SchemaFavorites], user = Depends(get_user)):
    db_favorites = []
    
    for favorite in favorites:
        if not project_exists(favorite.project_id):
            raise HTTPException(status_code=404,detail="Project not found")
        
        if not db.session.query(ModelHoursUser).filter(ModelHoursUser.id == favorite.user_id).first():
            raise HTTPException(status_code=400, detail="User not found")

        existing_favorite = db.session.query(ModelFavorites).filter(
            ModelFavorites.project_id == favorite.project_id,
            ModelFavorites.user_id == favorite.user_id,
        ).first()
           
        if existing_favorite:
            raise HTTPException(status_code=409, detail="Favorite already exists")

        db_favorite = ModelFavorites(
            project_id=favorite.project_id,
            user_id=favorite.user_id
        )

        db_favorites.append(db_favorite)

    db.session.add_all(db_favorites)
    db.session.commit()
    return db_favorites

# 1.8 Get favorites
@app.get("/favorites/{hours_user_id}",response_model=List[int])
async def get_favorites(hours_user_id: int , user = Depends(get_user)):

    if not db.session.query(ModelHoursUser).filter(ModelHoursUser.id == hours_user_id).first():
        raise HTTPException(status_code=400, detail="User not found")

    favorites =db.session.query(ModelFavorites.project_id).filter(
        ModelFavorites.user_id == hours_user_id
    ).all()

    projects_ids = [project_id for (project_id,) in favorites]
    return projects_ids

# 1.9 Delete favorites
@app.delete("/favorites")
async def delete_favorite(favorite: SchemaFavorites, user = Depends(get_user)):
    user_id = favorite.user_id
    project_id = favorite.project_id

    if not db.session.query(ModelHoursUser).filter(ModelHoursUser.id == user_id).first():
        raise HTTPException(status_code=400, detail="User not found")
    
    if not db.session.query(ModelProject).filter(ModelProject.id == project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")

    db_favorite = db.session.query(ModelFavorites).filter(
        ModelFavorites.user_id == user_id,
        ModelFavorites.project_id == project_id,
    ).first()

    if not db_favorite:
        raise HTTPException(status_code=404, detail="Project not defined as favorite by user")
    
    db.session.delete(db_favorite)
    db.session.commit()
    return {"message": "Favorite deleted"}

# 1.10 Get user domain
@app.get("/domain/{hours_user_id}",response_model=str)
async def get_domain(hours_user_id: int, user = Depends(get_user)):
    searched_user = db.session.query(ModelHoursUser).filter(ModelHoursUser.id == hours_user_id).first()
    
    if not searched_user:
        raise HTTPException(status_code=400, detail="User not found")
        
    searched_user_domain = str(searched_user.domain)    
    return searched_user_domain

# 1.11 Update user domain
@app.put("/domain/{hours_user_id}")
async def update_domain(hours_user_id: int, updated_domain: str, user = Depends(get_user)):
    
    domain_options = ['Acoustics','Tests','Hardware','Software','Mechanics']

    if updated_domain not in domain_options:
        raise HTTPException(status_code=400, detail="Wrong domain input")
    
    searched_user = db.session.query(ModelHoursUser).get(hours_user_id)
    
    if not searched_user:
        raise HTTPException(status_code=400, detail="User not found")
        
    searched_user.domain = str(updated_domain)
    db.session.commit()
    return {"message": "Domain updated"}


# 1.12 Input to buffer table
@app.post("/buffertable")
async def post_hours_per_day(dailyregs: List[SchemaBufferDailyRegister], user = Depends(get_user)):
    
    for dailyreg in dailyregs:

        if dailyreg.daily_hours > 0:
            buffer_rec = ModelBufferDailyRegister(
                user_id = dailyreg.user_id,
                day_date = dailyreg.day_date,
                project_id = dailyreg.project_id,
                daily_hours = dailyreg.daily_hours
            )
            
            db.session.add(buffer_rec)
        
        
    
    db.session.commit()
    return {"status":"buffer days registered"}


# 1.13 Get buffer table records
@app.get("/buffertable")
async def get_hours_per_day(hours_user_id: int, date_init: date, date_end: date, user = Depends(get_user)):
    searched_registers = db.session.query(ModelBufferDailyRegister).filter(
        ModelBufferDailyRegister.user_id == hours_user_id,
        ModelBufferDailyRegister.day_date.between(date_init, date_end)
        ).all()

    
    return searched_registers

# PART 2: METHODS FOR THE PROJECT MANAGER PROFILE
#____________________________________________________________________________________________________

# 2.1 Export records CSV 
@app.get("/export-csv")
async def export_csv(user = Depends(get_user)):
    result = db.session.query(ModelRecordProjects).all()
    column_names = ModelRecordProjects.__table__.columns.keys()

    csv_data = csv.DictWriter(open("export.csv","w"), fieldnames=column_names)
    csv_data.writeheader()
    for row in result:
       row_data = {fieldname: getattr(row, fieldname) for fieldname in column_names}
       csv_data.writerow(row_data)

    async with aiofiles.open("export.csv", mode="r") as f:
        contents = await f.read()

    return FileResponse("export.csv", filename="export.csv")

# 2.2 Import records from CSV 

@app.post("/import-csv")
async def import_csv(file: UploadFile = File(...)):
    
    contents = await file.read()
    csv_data = csv.DictReader(contents.decode("utf-8").splitlines())
    errors=[]

    for row in csv_data:
        user_id = int(row['user_id'])
        date_rec = datetime.datetime.strptime(row['date_rec'], '%Y-%m-%d').date()
        project_id = int(row['project_id'])
        declared_hours = int(row['declared_hours'])
        modified_hours = int(row['modified_hours'])

        if not date_rec.weekday() == 4:
            error_message = f"Records with the user_id {user_id} and date_rec {date_rec} are not valid: Incorrect date."
            errors.append(error_message)

        else:
            record_exists = db.session.query(ModelRecord).filter(
                                            ModelRecord.user_id == user_id,
                                            ModelRecord.date_rec == date_rec).first()
            
            if not record_exists:
                new_record = ModelRecord(
                    user_id = user_id,
                    date_rec = date_rec,
                    )
                
                db.session.add(new_record)
            
            new_record_project = ModelRecordProjects(
                    user_id = user_id,
                    date_rec = date_rec,
                    project_id = project_id,
                    declared_hours = declared_hours,
                    modified_hours = modified_hours)
            
            db.session.add(new_record_project)
    db.session.commit()
    return {"message": "Import successful."}

    
# 2.3 Add project
@app.post("/project",response_model=SchemaProject)
async def add_project(project: SchemaProject, user = Depends(get_user)):
    db_project = ModelProject(
        entity = project.entity,
        division = project.division,
        sub_category = project.sub_category,
        classification = project.classification,
        type = project.type,
        project_name = project.project_name,
        project_code = project.project_code,
        project_manager = project.project_manager,
        current_phase = project.current_phase,
        complexity = project.complexity,
        capitalization = project.capitalization
        )
    
    db.session.add(db_project)
    db.session.commit()
    return db_project

# 2.4 Modify project
@app.put("/project")
async def update_project(project: SchemaProject, user = Depends(get_user)):
           
    searched_project = db.session.query(ModelHoursUser).filter(project.id).first()
    
    if not searched_project:
        raise HTTPException(status_code=400, detail="Project not found")
    
    searched_project.entity = project.entity
    searched_project.division = project.division
    searched_project.sub_category = project.sub_category
    searched_project.classification = project.classification
    searched_project.type = project.type
    searched_project.project_name = project.project_name
    searched_project.project_code = project.project_code
    searched_project.project_manager = project.project_manager
    searched_project.current_phase = project.current_phase
    searched_project.complexity = project.complexity
    searched_project.capitalization = project.capitalization
        
    db.session.commit()
    return {"message": "Project updated"}


# 2.5 Change project phase

#Auxiliary functions
def project_exists(project_id: Union[int,str]) -> bool:
    project = db.session.query(ModelProject).get(project_id)
    return project is not None





