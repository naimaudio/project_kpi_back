from typing import Union, Annotated, Optional
import json
import base64
import os
import uvicorn
from fastapi import Depends, FastAPI , HTTPException, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sqlalchemy import DBSessionMiddleware,db
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, desc, text, asc, case, Date
from typing import List
import datetime
from datetime import date, timedelta
import csv
import aiofiles
from jose import jwt, jws, jwk
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


from schemas import HoursUserBase as SchemaHoursUserBase
from schemas import HoursUser as SchemaHoursUser
from schemas import BufferDailyRegister as SchemaBufferDailyRegister
from schemas import FrontEndUser as SchemaFrontEndUser
from schemas import Project as SchemaProject
from schemas import Record as SchemaRecord
from schemas import RecordProjects as SchemaRecordProjects
from schemas import Favorites as SchemaFavorites
from schemas import FrontendProjectPhase as SchemaProjectPhase
from schemas import MonthlyModifiedHours as SchemaMonthlyModifiedHours
from schemas import MonthlyForecast as SchemaMonthlyForecast

from models import HoursUser as ModelHoursUser
from models import Project as ModelProject
from models import Record as ModelRecord
from models import RecordProjects as ModelRecordProjects
from models import Favorites as ModelFavorites
from models import BufferDailyRegister as ModelBufferDailyRegister
from models import ProjectPhase as ModelProjectPhase
from models import MonthlyModifiedHours as ModelMonthlyModifiedHours
from models import MonthlyForecast as ModelMonthlyForecast

from database import SessionLocal
from dotenv import load_dotenv
load_dotenv(".env")
DISCOVERY_URL = os.getenv("DISCOVERY_URL")


app = FastAPI()

# Fetch the Azure public key
def get_azure_public_key():
    
    
    response=requests.get("https://login.microsoftonline.com/b6f16051-d990-480e-aa66-f95b1033a52b/.well-known/openid-configuration")
    if response.status_code == 200:
         data = response.json()
         print(data)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch public keys")


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


def wrap_jwk_public_key(jwk):
    # Extract the "n" (modulus) and "e" (exponent) from the JWK
    modulus = base64.urlsafe_b64decode(jwk["n"] + "==")
    exponent = base64.urlsafe_b64decode(jwk["e"] + "==")

    # Construct the RSA public key in ASN.1 format
    public_key_asn1 = (
        b"\x30\x0d\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01\x05\x00\x03"
        + b"\x81\x81\x00"
        + modulus
        + b"\x02\x03\x01\x00\x01\x03\x81\x81\x00"
        + exponent
    )

    # Convert the public key to Base64-encoded string
    public_key_base64 = base64.b64encode(public_key_asn1).decode("utf-8")

    # Wrap the Base64-encoded key with BEGIN and END headers
    
    wrapped_key = " ".join([public_key_base64[i:i+64] for i in range(0, len(public_key_base64), 64)])
    

    return wrapped_key




# Authentication Middleware
async def test_auth (token: str = Depends(oauth2_scheme)):
    response=requests.get("https://login.microsoftonline.com/b6f16051-d990-480e-aa66-f95b1033a52b/.well-known/openid-configuration")
    data = response.json()
    public_keys_uri = data
    public_keys = requests.get(public_keys_uri["jwks_uri"]).json()

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    alg = header.get("alg")

    key = next(key for key in public_keys["keys"] if key["kid"] == kid)
    modulus = base64.urlsafe_b64decode(key["n"] + "==")
    exponent_bytes = base64.urlsafe_b64decode(key["e"] + "==")
    exponent = int.from_bytes(exponent_bytes, byteorder="big", signed=False)
    mod = int.from_bytes(modulus, byteorder="big", signed=False)

    # Construct RSA public key
    public_numbers = rsa.RSAPublicNumbers(exponent, mod)
    public_key = public_numbers.public_key()

    # Serialize the RSA public key to PEM format
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Convert bytes to string and remove leading/trailing whitespaces
    pem_public_key_str = pem_public_key.decode("utf-8").strip()
    
    verif = jws.verify(token,pem_public_key,alg)
    #decoded_token = jwt_payload_decode(token)
    return pem_public_key_str




async def get_user (token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = jwt_payload_decode(token)
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


@app.get("/api/usertest")
async def get_usertest(user = Depends(test_auth)):
    return user


# 1.1 Get user /*/
@app.get("/api/user")
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

# 1.2 Get user ID /*/
@app.get("/api/userID")
async def get_user_ID(user: SchemaHoursUserBase = Depends(get_user)):
    
    if not user:
            raise HTTPException(status_code=400, detail="User not found")
    
    usermodel=db.session.query(ModelHoursUser).filter(ModelHoursUser.email  == user.email).first()
    
    return str(usermodel.id)


# 1.3 Insert record /*/
@app.post("/api/records")
async def insert_record(record: SchemaRecord, projects: List[SchemaRecordProjects], user: SchemaHoursUserBase = Depends(get_user)):
    
    userID = await get_user_ID(user)

    #Before everything: verify the user
    if not str(record.user_id) == userID:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    
    if record.date_rec.weekday() != 2:
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
    hourcount = 0.0
    
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

        if not project.declared_hours == 0.0:
            db_project = ModelRecordProjects(
                user_id = record.user_id,
                date_rec = record.date_rec,
                project_id = project.project_id,
                declared_hours = project.declared_hours
            )
            db_projects.append(db_project)

            searchedPhase=db.session.query(ModelProjectPhase).filter(
                ModelProjectPhase.project_id == project.project_id,
                ModelProjectPhase.start_date <= record.date_rec,
                ModelProjectPhase.end_date >= record.date_rec).first()
            
            if searchedPhase:
                searchedPhase.hours += project.declared_hours

            
        
        hourcount += project.declared_hours
   
    if hourcount != 35.0:
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


# 1.4 Get record /*/
@app.get("/api/records/{hours_user_id}")
async def get_records(hours_user_id: int, user: SchemaHoursUserBase = Depends(get_user)):
    
    ans = []

    if not db.session.query(ModelHoursUser).filter(ModelHoursUser.id == hours_user_id).first():
        raise HTTPException(status_code=400, detail="User not found")
    
    userID = await get_user_ID(user)
    
    if not str(hours_user_id) == userID:
        raise HTTPException(status_code=401, detail="Unauthorized access")

    user_declaredrecords = db.session.query(ModelRecord).filter(
        ModelRecord.user_id == hours_user_id).order_by(desc(ModelRecord.date_rec)).all()
    
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



# 1.5 Get projects /*/
@app.get("/api/projects",response_model=List[SchemaProject])
async def get_projects(user = Depends(get_user)):
    projects =db.session.query(ModelProject).all()
    if not projects:
            raise HTTPException(status_code=404,detail="No projects on database")
    return projects

# 1.6 Define favorites /*/
@app.post("/api/favorites",response_model=List[SchemaFavorites])
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

# 1.8 Get favorites /*/
@app.get("/api/favorites/{hours_user_id}",response_model=List[int])
async def get_favorites(hours_user_id: int , user = Depends(get_user)):

    if not db.session.query(ModelHoursUser).filter(ModelHoursUser.id == hours_user_id).first():
        raise HTTPException(status_code=400, detail="User not found")

    favorites =db.session.query(ModelFavorites.project_id).filter(
        ModelFavorites.user_id == hours_user_id
    ).all()

    projects_ids = [project_id for (project_id,) in favorites]
    return projects_ids

# 1.9 Delete favorites /*/
@app.delete("/api/favorites")
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

# 1.10 Get user domain /*/
@app.get("/api/domain/{hours_user_id}",response_model=str)
async def get_domain(hours_user_id: int, user = Depends(get_user)):
    searched_user = db.session.query(ModelHoursUser).filter(ModelHoursUser.id == hours_user_id).first()
    
    if not searched_user:
        raise HTTPException(status_code=400, detail="User not found")
        
    searched_user_domain = str(searched_user.domain)    
    return searched_user_domain

# 1.11 Update user domain /*/
@app.put("/api/domain/{hours_user_id}")
async def update_domain(hours_user_id: int, updated_domain: str, user = Depends(get_user)):
    
    domain_options = ['Acoustics','Tests','Hardware','Software','Mechanics','Project Management']

    if updated_domain not in domain_options:
        raise HTTPException(status_code=400, detail="Wrong domain input")
    
    searched_user = db.session.query(ModelHoursUser).get(hours_user_id)
    
    if not searched_user:
        raise HTTPException(status_code=400, detail="User not found")
        
    searched_user.domain = str(updated_domain)
    db.session.commit()
    return {"message": "Domain updated"}


# 1.12 Input to buffer table /*/
@app.post("/api/buffertable")
async def post_hours_per_day(dailyregs: List[SchemaBufferDailyRegister], user = Depends(get_user)):
    
    for dailyreg in dailyregs:
        searched_records = db.session.query(ModelBufferDailyRegister).filter(
            ModelBufferDailyRegister.user_id == dailyreg.user_id,
            ModelBufferDailyRegister.day_date == dailyreg.day_date,
            ).all()
        
        for buffer_record in searched_records:
            db.session.delete(buffer_record)
    
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


# 1.13 Get buffer table records /*/
@app.get("/api/buffertable")
async def get_hours_per_day(hours_user_id: int, date_init: date, date_end: date, user = Depends(get_user)):
    searched_registers = db.session.query(ModelBufferDailyRegister).filter(
        ModelBufferDailyRegister.user_id == hours_user_id,
        ModelBufferDailyRegister.day_date.between(date_init, date_end)
        ).all()

    
    return searched_registers

# PART 2: METHODS FOR THE PROJECT MANAGER PROFILE
#____________________________________________________________________________________________________

# 2.1 Export records CSV 
@app.get("/api/export-records-csv")
async def export_csv():
    result = db.session.query(ModelRecordProjects).all()
    column_names = ["user_email",
                    "week",
                    "year",
                    "project_code",
                    "declared_hours"]

    csv_data = csv.DictWriter(open("export.csv","w"), fieldnames=column_names,delimiter=";")
    csv_data.writeheader()
    for row in result:
        user_email=getattr(db.session.query(ModelHoursUser).filter(
            ModelHoursUser.id == getattr(row,"user_id")).first(),"email")
        date_rec=getattr(row,"date_rec")
        week=date_rec.isocalendar()[1]
        year=date_rec.year
        project_code=getattr(db.session.query(ModelProject).filter(
            ModelProject.id == getattr(row,"project_id")).first(),"project_code")
        declared_hours=getattr(row,"declared_hours")
        to_add=[user_email,
                    week,
                    year,
                    project_code,
                    declared_hours]

        row_data = {"user_email":user_email,
                    "week":week,
                    "year":year,
                    "project_code":project_code,
                    "declared_hours":declared_hours}      
        csv_data.writerow(row_data)

    async with aiofiles.open("export.csv", mode="r") as f:
        contents = await f.read()

    return FileResponse("export.csv", filename="export.csv")

# 2.2 Import records from CSV 

@app.post("/api/import-csv")
async def import_csv(file: UploadFile = File(...)):
    
    contents = await file.read()
    csv_data = csv.DictReader(contents.decode("utf-8").splitlines(),delimiter=";")
    errors=[]

    for row in csv_data:
        user_email = str(row['user_email'])
        week = int(row['week'])
        year = int(row['year'])
        project_code = str(row['project_code'])
        declared_hours = float(row['declared_hours'])

        date_rec = datetime.date.fromisocalendar(year,week,3)
        
        searched_user = db.session.query(ModelHoursUser).filter(
                                        ModelHoursUser.email == user_email).first()
        
        if not searched_user:
            raise HTTPException(status_code=400, detail="User "+ user_email + " not found")
        
        user_id = getattr(searched_user,"id")
        
        searched_project = db.session.query(ModelProject).filter(
                                        ModelProject.project_code == project_code).first()
        
        if not searched_project:
            raise HTTPException(status_code=400, detail="Project "+ project_code + " not found")
        

        project_id = getattr(searched_project,"id")
        
        
        
        
        existing_record_project=db.session.query(ModelRecordProjects).filter(
                                        ModelRecordProjects.user_id == user_id,
                                        ModelRecordProjects.date_rec == date_rec,
                                        ModelRecordProjects.project_id == project_id).first()



        record_exists = db.session.query(ModelRecord).filter(
                                        ModelRecord.user_id == user_id,
                                        ModelRecord.date_rec == date_rec).first()
            
        if not record_exists:
            new_record = ModelRecord(
            user_id = user_id,
            date_rec = date_rec,
            )
                
            db.session.add(new_record)
        else:
            if existing_record_project:
                db.session.delete(existing_record_project)

            
        new_record_project = ModelRecordProjects(
            user_id = user_id,
            date_rec = date_rec,
            project_id = project_id,
            declared_hours = declared_hours)
            
        db.session.add(new_record_project)
    db.session.commit()
    return {"message": "Import successful."}

    
# 2.3 Add project
@app.post("/api/project")
async def add_project(project: SchemaProject, phases: List[SchemaProjectPhase], forecasts: List[SchemaMonthlyForecast]):

    existing_code = db.session.query(ModelProject).filter(ModelProject.project_code == project.project_code).first() 
    
    if existing_code:
        raise HTTPException(status_code=400, detail="Project code already exists")
    
    db_project = ModelProject(
        entity = project.entity,
        division = project.division,
        sub_category = project.sub_category,
        classification = project.classification,
        type = project.type,
        project_name = project.project_name,
        project_code = project.project_code,
        project_manager = project.project_manager,
        complexity = project.complexity,
        start_cap_date = project.start_cap_date,
        end_cap_date = project.end_cap_date,
        start_date = project.start_date,
        end_date = project.end_date
        )
    
    db.session.add(db_project)
    
    projectid = getattr(db.session.query(ModelProject).filter(ModelProject.project_code == project.project_code).first(),"id")

    for phase in phases:
     
        db_phase = ModelProjectPhase(
            project_id = projectid,
            project_phase = phase.project_phase,
            start_date = phase.start_date,
            end_date = phase.end_date
            )
        
        db.session.add(db_phase)
    
    for forecast in forecasts:
        
        if forecast.month is not None and forecast.year is not None:
            forecast_date = datetime.date(forecast.year, forecast.month, 1)
        else:
            raise HTTPException(status_code=400, detail="Invalid date") 


        db_forecast = ModelMonthlyForecast(
            project_id = projectid,
            month = forecast_date,
            hours = forecast.hours
            )
        
        db.session.add(db_forecast)

    db.session.commit()
    
    return {'message: Project with phases added successfully'}


getprojectmodel={'project': SchemaProject,
            "phases":List[SchemaProjectPhase]} 

# 2.3.1 Get project /*/
@app.get("/api/project")
async def get_project_with_phases(projectcode: str):
    
    modelproject =db.session.query(ModelProject).filter(
        ModelProject.project_code == projectcode
    ).first()

    if not modelproject:
            raise HTTPException(status_code=404,detail="Project does not exist")
    
    project = SchemaProject(
        id = modelproject.id,
        entity = modelproject.entity,
        division = modelproject.division,
        sub_category= modelproject.sub_category,
        classification= modelproject.classification, 
        type= modelproject.type,
        project_name= modelproject.project_name,
        project_code= modelproject.project_code,
        project_manager= modelproject.project_manager,
        complexity= modelproject.complexity,
        start_cap_date = modelproject.start_cap_date,
        end_cap_date = modelproject.end_cap_date,
        start_date = modelproject.start_date,
        end_date = modelproject.end_date
    )

    phases_ans=[]

    projectid=getattr(project,"id")

    phases = db.session.query(ModelProjectPhase).filter(
        ModelProjectPhase.project_id == projectid
    )

    if phases:
        for phase in phases:
            frontend_phase=SchemaProjectPhase(
                project_phase = phase.project_phase, 
                start_date = phase.start_date,
                end_date = phase.end_date
            )
            phases_ans.append(frontend_phase)

    forecasts_ans=[]

    forecasts = db.session.query(ModelMonthlyForecast).filter(
        ModelMonthlyForecast.project_id == projectid
    )
    
    if forecasts:
        for forecast in forecasts:
            frontend_forecast=SchemaMonthlyForecast(
                project_id = projectid,
                month = forecast.month.month,
                year = forecast.month.year,
                hours = forecast.hours
            )
            forecasts_ans.append(frontend_forecast)


    return {'project': project,
            "phases":phases_ans,
            "forecasts":forecasts_ans} 



# 2.4 Modify project
@app.put("/api/project")
async def update_project(project: SchemaProject, phases: List[SchemaProjectPhase], forecasts: List[SchemaMonthlyForecast]):
           
    searched_project = db.session.query(ModelProject).filter(ModelProject.id == project.id).first()

    existing_code = db.session.query(ModelProject).filter(ModelProject.project_code == project.project_code).first() 
    
    if existing_code:
        if not (existing_code.project_code == searched_project.project_code):
            raise HTTPException(status_code=400, detail="Project code already exists")
    
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
    searched_project.complexity = project.complexity
    searched_project.start_cap_date = project.start_cap_date
    searched_project.end_cap_date = project.end_cap_date
    searched_project.start_date = project.start_date
    searched_project.end_date = project.end_date
        
    db.session.commit()


    searched_phases = db.session.query(ModelProjectPhase).filter(
        ModelProjectPhase.project_id == project.id)

    for searched_phase in searched_phases:
        db.session.delete(searched_phase)
    
    db.session.commit()
    
    for phase in phases:

        db_phase = ModelProjectPhase(
            project_id = project.id,
            project_phase = phase.project_phase,
            start_date = phase.start_date,
            end_date = phase.end_date
            )
    
        db.session.add(db_phase)
    
    db.session.commit()

    update_project_phase_hours(project.id)

    searched_forecasts = db.session.query(ModelMonthlyForecast).filter(
        ModelMonthlyForecast.project_id == project.id)
    
    for searched_forecast in searched_forecasts:
        db.session.delete(searched_forecast)

    for forecast in forecasts:

        if forecast.month is not None and forecast.year is not None:
            forecast_date = datetime.date(forecast.year, forecast.month, 1)
        else:
            raise HTTPException(status_code=400, detail="Invalid date") 

        db_forecast = ModelMonthlyForecast(
            project_id = project.id,
            month = forecast_date,
            hours = forecast.hours
            )
    
        db.session.add(db_forecast)
    
    db.session.commit()


    return {"message": "Project updated"}


# 2.5 Delete project
@app.delete("/api/project")
async def delete_project(project_code: str, user: SchemaHoursUserBase = Depends(get_user)):
      
    project_id = getattr(db.session.query(ModelProject).filter(ModelProject.project_code==project_code).first(),"id")
    
    if not validateManagers(False,user):
        raise HTTPException(status_code=401, detail="Unauthorized access")
    
    searched_project = db.session.query(ModelProject).filter(ModelProject.id == project_id).first()
    
    if not searched_project:
        raise HTTPException(status_code=400, detail="Project not found")
    
    message="Project not deleted. Please erase the records associated to the project first."
    
    records_in_project=db.session.query(ModelRecordProjects).filter(
        ModelRecordProjects.project_id == project_id 
    ).first()
        
    if not records_in_project:
        
        to_delete_phases = db.session.query(ModelProjectPhase).filter(ModelProjectPhase.project_id == project_id).all()
        to_delete_forecasts = db.session.query(ModelMonthlyForecast).filter(ModelMonthlyForecast.project_id == project_id).all()
        
        for phase in to_delete_phases:
            db.session.delete(phase)
            db.session.commit()

        for forecast in to_delete_forecasts:
            db.session.delete(forecast)
            db.session.commit()

        db.session.delete(searched_project)
        message="Project deleted."
        db.session.commit()


    
        
   
    return {"message": message}

# 2.6 Add project phase
@app.post("/api/phase")
async def add_phase(phase: SchemaProjectPhase, projectcode: str):
    
    try:
        projectid = getattr(db.session.query(ModelProject).filter(ModelProject.project_code == projectcode).first(),"id")
    
    except Exception as e :
        raise HTTPException(status_code=400, detail="Invalid project code")
    
        
    
    
    db_phase = ModelProjectPhase(
            project_id = projectid,
            project_phase = phase.project_phase,
            start_date = phase.start_date,
            end_date = phase.end_date,
            records=0
            )
    
    db.session.add(db_phase)
    db.session.commit()

    update_project_phase_hours(projectid)
    
    return {"message": "Phase registered successfully"}

# 2.7 Change project phase
@app.put("/api/phase")
async def change_phase(phase: SchemaProjectPhase, projectcode: str):

    projectid = getattr(db.session.query(ModelProject).filter(ModelProject.project_code == projectcode).first(),"id")

    if not projectid:
        raise HTTPException(status_code=400, detail="Project not found")

    searched_phase = db.session.query(ModelProjectPhase).filter(
        ModelProjectPhase.project_id == projectid,
        ModelProjectPhase.project_phase == phase.project_phase).first()
    
    if not searched_phase:
        raise HTTPException(status_code=400, detail="Phase not found")
    
    searched_phase.project_id = projectid,
    searched_phase.project_phase = phase.project_phase,
    searched_phase.start_date = phase.start_date,
    searched_phase.end_date = phase.end_date,

    db.session.commit()

    update_project_phase_hours(projectid)
    
    return {"message": "Phase modified successfully"}

# 2.8 Delete project phase
@app.delete("/api/phase")
async def delete_phase(phase: int, projectcode: str):

    projectid = getattr(db.session.query(ModelProject).filter(ModelProject.project_code == projectcode).first(),"id")

    if not projectid:
        raise HTTPException(status_code=400, detail="Project not found")

    searched_phase = db.session.query(ModelProjectPhase).filter(
        ModelProjectPhase.project_id == projectid,
        ModelProjectPhase.project_phase == phase).first()
    
    if not searched_phase:
        raise HTTPException(status_code=400, detail="Phase not found")
    
    message="Phase not deleted. Please erase the records associated to the phase first."
    
    records_in_phase=db.session.query(ModelRecordProjects).filter(
        ModelRecordProjects.project_id == projectid,
        ModelRecordProjects.date_rec >= searched_phase.start_date,
        ModelRecordProjects.date_rec <= searched_phase.end_date
    ).first()
        
    if not records_in_phase:
        db.session.delete(searched_phase)
        message="Phase deleted."

    update_project_phase_hours(projectid)
        
    db.session.commit()


    return {"message": message}

# KPIs

# 2.9. KPI pie chart
@app.get("/api/kpi/pie/hours_by_domain")
async def kpi_piedomainhours( project_id: int, 
        unit: str, 
        month1: Optional[int] = None,
        year1: Optional[int] = None,
        month2: Optional[int] = None,
        year2: Optional[int] = None,
        user: SchemaHoursUserBase = Depends(get_user)
    ):
    
    start_date = None
    end_date = None

    if month1 is not None and year1 is not None:
        start_date = datetime.date(year1, month1, 1)

    if month2 is not None and year2 is not None:
        if month2 == 12:
            end_date = datetime.date(year2 + 1, 1, 1)
        else:
            end_date = datetime.date(year2, month2 + 1, 1)


    if start_date:
        if end_date:
            result = (db.session.query(ModelHoursUser.domain, func.sum(ModelRecordProjects.declared_hours))
              .filter(
            ModelRecordProjects.project_id == project_id,
            ModelRecordProjects.date_rec >= start_date,
            ModelRecordProjects.date_rec < end_date
            ).join(ModelRecord, ModelHoursUser.id == ModelRecord.user_id)
            .join(ModelRecordProjects,(ModelRecord.date_rec == ModelRecordProjects.date_rec) & (ModelRecord.user_id == ModelRecordProjects.user_id) )
            .group_by(ModelHoursUser.domain).all())
        else:
            result = (db.session.query(ModelHoursUser.domain, func.sum(ModelRecordProjects.declared_hours))
              .filter(
            ModelRecordProjects.project_id == project_id,
            ModelRecordProjects.date_rec >= start_date,
            ).join(ModelRecord, ModelHoursUser.id == ModelRecord.user_id)
            .join(ModelRecordProjects,(ModelRecord.date_rec == ModelRecordProjects.date_rec) & (ModelRecord.user_id == ModelRecordProjects.user_id) )
            .group_by(ModelHoursUser.domain).all())
    elif end_date:
        result = (db.session.query(ModelHoursUser.domain, func.sum(ModelRecordProjects.declared_hours))
              .filter(
            ModelRecordProjects.project_id == project_id,
            ModelRecordProjects.date_rec < end_date
            ).join(ModelRecord, ModelHoursUser.id == ModelRecord.user_id)
            .join(ModelRecordProjects,(ModelRecord.date_rec == ModelRecordProjects.date_rec) & (ModelRecord.user_id == ModelRecordProjects.user_id) )
            .group_by(ModelHoursUser.domain).all())
    else:
        result = (db.session.query(ModelHoursUser.domain, func.sum(ModelRecordProjects.declared_hours))
              .filter(
            ModelRecordProjects.project_id == project_id
            ).join(ModelRecord, ModelHoursUser.id == ModelRecord.user_id)
            .join(ModelRecordProjects,(ModelRecord.date_rec == ModelRecordProjects.date_rec) & (ModelRecord.user_id == ModelRecordProjects.user_id) )
            .group_by(ModelHoursUser.domain).all())
    
    
    
    
    factor = 1
    if(unit=='TDE'):
        factor=140
    else:
        if not unit=='h':
            raise HTTPException(status_code=401, detail="Invalid units")


    declared_hours_by_domain = {domain: declared_hours/factor for domain, declared_hours in result}



    return {
        'unit':'h',
        'series':[
            {
                "data": declared_hours_by_domain,
                "name": "Spent hours by domain",
                "type": 'pie'
            }
        ]
    }

#2.10 KPI Line graph
@app.get("/api/kpi/line/hour_expenditure")
async def kpi_linehours(
        project_id: int, 
        cumulative: bool, 
        unit: str, 
        month1: Optional[int] = None,
        year1: Optional[int] = None,
        month2: Optional[int] = None,
        year2: Optional[int] = None,
        user: SchemaHoursUserBase = Depends(get_user)
    ):
    
    start_date = None
    end_date = None

    if month1 is not None and year1 is not None:
        start_date = datetime.date(year1, month1, 1)

    if month2 is not None and year2 is not None:
        if month2 == 12:
            end_date = datetime.date(year2 + 1, 1, 1)
        else:
            end_date = datetime.date(year2, month2 + 1, 1)

    if start_date:
        
        if end_date:
            result = (
            db.session.query(
                func.to_char(func.DATE_TRUNC('month', ModelRecordProjects.date_rec), 'YYYY-MM').label('date'),
                func.sum(ModelRecordProjects.declared_hours).label('hours')
            ).filter(ModelRecordProjects.project_id == project_id,
                    ModelRecordProjects.date_rec >= start_date,
                    ModelRecordProjects.date_rec < end_date
                    )
            .group_by(func.DATE_TRUNC('month', ModelRecordProjects.date_rec))
            .order_by(text("DATE_TRUNC('month', date_rec) ASC"))
            .all()
            )

        else:
            result = (
                db.session.query(
                    func.to_char(func.DATE_TRUNC('month', ModelRecordProjects.date_rec), 'YYYY-MM').label('date'),
                    func.sum(ModelRecordProjects.declared_hours).label('hours')
                ).filter(ModelRecordProjects.project_id == project_id,
                        ModelRecordProjects.date_rec >= start_date
                        )
                .group_by(func.DATE_TRUNC('month', ModelRecordProjects.date_rec))
                .order_by(text("DATE_TRUNC('month', date_rec) ASC"))
                .all()
                )
    elif end_date:
        result = (
            db.session.query(
                func.to_char(func.DATE_TRUNC('month', ModelRecordProjects.date_rec), 'YYYY-MM').label('date'),
                func.sum(ModelRecordProjects.declared_hours).label('hours')
            ).filter(ModelRecordProjects.project_id == project_id,
                    ModelRecordProjects.date_rec < end_date
                    )
            .group_by(func.DATE_TRUNC('month', ModelRecordProjects.date_rec))
            .order_by(text("DATE_TRUNC('month', date_rec) ASC"))
            .all()
            )
    else:
        result = (
        db.session.query(
            func.to_char(func.DATE_TRUNC('month', ModelRecordProjects.date_rec), 'YYYY-MM').label('date'),
            func.sum(ModelRecordProjects.declared_hours).label('hours')
        ).filter(ModelRecordProjects.project_id == project_id
                )
        .group_by(func.DATE_TRUNC('month', ModelRecordProjects.date_rec))
        .order_by(text("DATE_TRUNC('month', date_rec) ASC"))
        .all()
        )

    # Convert the result into a list of dictionaries
    dates = [row.date for row in result]
    hours = [row.hours for row in result]
    
    if(unit=='TDE'):
        TDEs=[row/140 for row in hours]
        hours=TDEs
    else:
        if not unit=='h':
            raise HTTPException(status_code=401, detail="Invalid units")

    if cumulative:
        cumhours = []
        cumsum=0
        for hour in hours:
            cumsum += hour
            cumhours.append(cumsum)
        hours=cumhours

    return {
        'unit':unit,
        'xAxis': {"data":dates},
        'series':[
            {
                "data": hours,
                "name": "Spent",
                "type": 'line'
            }
        ],
        'legend': {
            'data': ["Spent"]
        }
    }

#2.11 KPI Stacked bar chart
@app.get("/api/kpi/stackedbar/hour_expenditure_by_project")
async def kpi_stackedbar(        
        project_id: int,
        unit: str,
        user: SchemaHoursUserBase = Depends(get_user)
    ):

    
    stackedbar=[]
    phases=[]

    factor = 1
    if(unit=='TDE'):
        factor=140
    else:
        if not unit=='h':
            raise HTTPException(status_code=401, detail="Invalid units")
        
    result = (
        db.session.query(
            ModelProjectPhase.project_phase,ModelProjectPhase.hours
        ).filter(ModelProjectPhase.project_id == project_id).all()
        )

    for res in result:
                       
        to_add={
            "data": [res.hours/factor],
            "name": res.project_phase,
            "type": "bar"
        }
        
        stackedbar.append(to_add)
        phases.append(res.project_phase)

    return {
        'unit':unit,
        'yAxis': {"data": ["Time spent"]},
        'series':stackedbar,
        'legend':{'data':phases}
    }






# PART 3: METHODS FOR THE BUSINESS MANAGER PROFILE
#____________________________________________________________________________________________________

#3.1. Get monthly hours
@app.get("/api/monthlyhours",response_model=List[SchemaMonthlyModifiedHours])
async def get_monthly_hours(month:int, year:int, user = Depends(get_user)):
    
    # Getting the current date and time
    
    ans=[]
    
    dateM=datetime.date(year,month,1)

    filtered_users=db.session.query(ModelMonthlyModifiedHours.user_id).filter(ModelMonthlyModifiedHours.month == dateM).distinct().all()
    
    for user in filtered_users:
        
        username = getattr(db.session.query(ModelHoursUser).filter(ModelHoursUser.id == user.user_id).first(),"username")
       
        hourslist=[]

        records_with_user=db.session.query(ModelMonthlyModifiedHours).filter(ModelMonthlyModifiedHours.month == dateM,
                                                                             ModelMonthlyModifiedHours.user_id == user.user_id)

        for record in records_with_user:
            if not record.total_hours == 0:
                proj={"project_id":record.project_id,
                    "hours":record.total_hours}
                hourslist.append(proj)               
                

        sch=SchemaMonthlyModifiedHours(
            user_id=user.user_id,
            user_name=username,
            hours=hourslist
        )
        ans.append(sch)

    return ans


#3.2. Modify monthly hours
@app.put("/api/monthlyhours")
async def change_monthly_hours(month:int, year:int, changed_records:List[SchemaMonthlyModifiedHours]):
    
    dateM=datetime.date(year,month,1)

    for change in changed_records:
        user_id = getattr(db.session.query(ModelMonthlyModifiedHours).filter(
                ModelMonthlyModifiedHours.user_id==change.user_id).first(),"user_id")


        for project in change.hours:
            searched_record=db.session.query(ModelMonthlyModifiedHours).filter(
                ModelMonthlyModifiedHours.project_id==project["project_id"],
                ModelMonthlyModifiedHours.month==dateM,
                ModelMonthlyModifiedHours.user_id==user_id).first()
            
            if not searched_record:
                db_monthlyhour = ModelMonthlyModifiedHours(
                    user_id = user_id,
                    project_id = project["project_id"],
                    month = dateM,
                    total_hours = project["hours"]
                )
        
                db.session.add(db_monthlyhour)
            
            
            else:
                searched_record.total_hours = project["hours"]
            
            db.session.commit()
    
   
    return {"message":"Hours modified successfully"}


#3.3. Update monthly hours' table
@app.post("/api/monthlyhours")
async def update_monthly_hours(month:int, year:int):
    
    dateM=datetime.date(year,month,1)
    dateFin=datetime.date(year,month+1,2)
 
    existingMonthlyHours= db.session.query(ModelMonthlyModifiedHours).filter(
        ModelMonthlyModifiedHours.month == dateM
    ).all()

    if existingMonthlyHours:
        for rec in existingMonthlyHours:
            db.session.delete(rec)
            db.session.commit()
    
    
    subquery = db.session.query(
        ModelRecordProjects.user_id,
        ModelRecordProjects.project_id,
        func.date_trunc('month', dateM).label('month'),
        func.sum(
            case(
                (func.date_trunc('month', func.cast(
                                ModelRecordProjects.date_rec, 
                                Date
                            )) == dateM,ModelRecordProjects.declared_hours)),
                else_=0.0
            ).label('total_hours')
        ).filter(
            ModelRecordProjects.date_rec >= dateM,
            ModelRecordProjects.date_rec <= dateFin
    ).group_by(
        ModelRecordProjects.user_id,
        ModelRecordProjects.project_id,
        func.date_trunc('month', dateM)
    ).all()
    
    
    
    for row in subquery:
        
        db_monthlyhour = ModelMonthlyModifiedHours(
                user_id = row.user_id,
                project_id = row.project_id,
                month = dateM,
                total_hours = row.total_hours
                )
        
        db.session.add(db_monthlyhour)
        db.session.commit()

  
    return {"message":"Table updated successfully"}



#3.4. Business KPIs: capitalization summary




















#3.x. Business KPIs: line
@app.get("/api/business_kpi/line/hour_expenditure")
async def businesskpi_linehours(
        cumulative:bool, 
        unit: str, 
        month1: Optional[int] = None,
        year1: Optional[int] = None,
        month2: Optional[int] = None,
        year2: Optional[int] = None,
        user: SchemaHoursUserBase = Depends(get_user)):
    
    
    start_date = None
    end_date = None

    if month1 is not None and year1 is not None:
        start_date = datetime.date(year1, month1, 1)

    if month2 is not None and year2 is not None:
        if month2 == 12:
            end_date = datetime.date(year2 + 1, 1, 1)
        else:
            end_date = datetime.date(year2, month2 + 1, 1)
        
    
    if start_date:
        if end_date:
            result = (
            db.session.query(
                ModelMonthlyModifiedHours.month.label('date'),
                func.sum(ModelMonthlyModifiedHours.total_hours).label('hours')
            )
            .filter(ModelMonthlyModifiedHours.month >= start_date,
                    ModelMonthlyModifiedHours.month < end_date)
            .group_by(ModelMonthlyModifiedHours.month)
            .order_by(ModelMonthlyModifiedHours.month)
            .all()
            )
        else: 
            result = (
            db.session.query(
                ModelMonthlyModifiedHours.month.label('date'),
                func.sum(ModelMonthlyModifiedHours.total_hours).label('hours')
            )
            .filter(ModelMonthlyModifiedHours.month >= start_date)
            .group_by(ModelMonthlyModifiedHours.month)
            .order_by(ModelMonthlyModifiedHours.month)
            .all()
            )
    elif end_date: result = (
            db.session.query(
                ModelMonthlyModifiedHours.month.label('date'),
                func.sum(ModelMonthlyModifiedHours.total_hours).label('hours')
            )
            .filter(ModelMonthlyModifiedHours.month < end_date)
            .group_by(ModelMonthlyModifiedHours.month)
            .order_by(ModelMonthlyModifiedHours.month)
            .all()
            )
    else:
        result = (
            db.session.query(
                ModelMonthlyModifiedHours.month.label('date'),
                func.sum(ModelMonthlyModifiedHours.total_hours).label('hours')
            )
            .group_by(ModelMonthlyModifiedHours.month)
            .order_by(ModelMonthlyModifiedHours.month)
            .all()
            )
    
   

       

    # Convert the result into a list of dictionaries
    dates = [row.date for row in result]
    hours = [row.hours for row in result]

    if cumulative:
        cumhours = []
        cumsum=0
        for hour in hours:
            cumsum += hour
            cumhours.append(cumsum)
        hours=cumhours

    if(unit=='TDE'):
        TDEs=[row/140 for row in hours]
        hours=TDEs
    else:
        if not unit=='h':
            raise HTTPException(status_code=401, detail="Invalid units")


    return {
        'unit':'h',
        'xAxis': {"data":dates},
        'series':[
            {
                "data": hours,
                "name": "Spent",
                "type": 'line'
            }
        ],
        'legend': {
            'data': ["Spent"]
        }
    }

#3.x. Business KPIs: pie
@app.get("/api/business_kpi/pie/hours_by_domain")
async def businesskpi_piedomainhours(
    unit: str, 
    month1: Optional[int] = None,
    year1: Optional[int] = None,
    month2: Optional[int] = None,
    year2: Optional[int] = None,
    user: SchemaHoursUserBase = Depends(get_user)):

    start_date = None
    end_date = None

    if month1 is not None and year1 is not None:
        start_date = datetime.date(year1, month1, 1)

    if month2 is not None and year2 is not None:
        if month2 == 12:
            end_date = datetime.date(year2 + 1, 1, 1)
        else:
            end_date = datetime.date(year2, month2 + 1, 1)

    if start_date:
        if end_date:
            result = (db.session.query(ModelHoursUser.domain, func.sum(ModelMonthlyModifiedHours.total_hours))
                .filter(
                ModelMonthlyModifiedHours.month >= start_date,
                ModelMonthlyModifiedHours.month < end_date)
                .join(ModelMonthlyModifiedHours, ModelHoursUser.id == ModelMonthlyModifiedHours.user_id)
                .group_by(ModelHoursUser.domain).all())
        else:
            result = (db.session.query(ModelHoursUser.domain, func.sum(ModelMonthlyModifiedHours.total_hours))
                .filter(ModelMonthlyModifiedHours.month >= start_date)
                .join(ModelMonthlyModifiedHours, ModelHoursUser.id == ModelMonthlyModifiedHours.user_id)
                .group_by(ModelHoursUser.domain).all())
    elif end_date:
        result = (db.session.query(ModelHoursUser.domain, func.sum(ModelMonthlyModifiedHours.total_hours))
                .filter(ModelMonthlyModifiedHours.month < end_date)
                .join(ModelMonthlyModifiedHours, ModelHoursUser.id == ModelMonthlyModifiedHours.user_id)
                .group_by(ModelHoursUser.domain).all())
    else:
        result = (db.session.query(ModelHoursUser.domain, func.sum(ModelMonthlyModifiedHours.total_hours))
                .join(ModelMonthlyModifiedHours, ModelHoursUser.id == ModelMonthlyModifiedHours.user_id)
                .group_by(ModelHoursUser.domain).all())

    

    factor = 1
    if(unit=='TDE'):
        factor=140
    else:
        if not unit=='h':
            raise HTTPException(status_code=401, detail="Invalid units")

    declared_hours_by_domain = {domain: declared_hours/factor for domain, declared_hours in result}

    return {
        'unit':'h',
        'series':[
            {
                "data": declared_hours_by_domain,
                "name": "Spent hours by domain",
                "type": 'pie'
            }
        ]
    }

#3.x. Get users
@app.get("/api/getusers")
async def get_all_users():
    ans=[]
    users =db.session.query(ModelHoursUser).all()
    if not users:
            raise HTTPException(status_code=404,detail="No users on database")
    
    for user in users:
        db_user={
            "name": user.username,
            "id": user.id,
            "email":user.email}
        
        ans.append(db_user)
    return ans


#___________________________________________________________________________________________

#Auxiliary functions
def project_exists(project_id: Union[int,str]) -> bool:
    project = db.session.query(ModelProject).get(project_id)
    return project is not None

def validateManagers(BM: bool, user: SchemaHoursUserBase= Depends(get_user)):
    usertype = getattr(db.session.query(ModelHoursUser).filter(
        ModelHoursUser.username == user.username,
        ModelHoursUser.email == user.email).first(),"role")

    res=False

    if not BM:
        if (usertype=="Project Manager" or usertype=="Business Manager"):
            res=True
    else:
        if (usertype=="Business Manager"):
            res=True
    return res

def find_capitalization(project_phase: int):
    res = None
    
    if not (project_phase >=0 and project_phase <=7):
        raise HTTPException(status_code=401, detail="Invalid project phase")
    
    if project_phase <= 2:
        res = False
    else:
        res = True

    return res

def week_in_month(month, record_date):
    # Get the Monday and Wednesday of the week corresponding to the record_date
    monday = record_date - timedelta(days=record_date.weekday())
    wednesday = monday + timedelta(days=2)

    # Check if both Monday and Wednesday belong to the same month as the given month
    cond = (
        (monday.year, monday.month) == (month.year, month.month) and
        (wednesday.year, wednesday.month) == (month.year, month.month)
    )

    return cond

def update_project_phase_hours(project_id):
    # Create a session to interact with the database
    try:
        # Query ProjectPhases for the specific project_id
        phases = db.session.query(ModelProjectPhase).filter(ModelProjectPhase.project_id == project_id).all()

        # Loop through each phase and calculate the summed hours from RecordProjects
        for phase in phases:
            start_date = phase.start_date
            end_date = phase.end_date

            # Query RecordProjects and sum the declared_hours within the date interval
            total_hours = db.session.query(func.sum(ModelRecordProjects.declared_hours)).filter(
                ModelRecordProjects.project_id == project_id,
                ModelRecordProjects.date_rec >= start_date,
                ModelRecordProjects.date_rec < end_date
            ).scalar()

            # Update the hours column of the ProjectPhases with the calculated total_hours
            phase.hours = total_hours

        # Commit the changes to the database
        db.session.commit()

    except Exception as e:
        raise HTTPException(status_code=404, detail="Unable to update hours")


#add: change monthly hours from csv
@app.put("/api/import-csv-monthly")
async def import_csv_monthly(file: UploadFile = File(...)):
    
    contents = await file.read()
    csv_data = csv.DictReader(contents.decode("utf-8").splitlines(),delimiter=";")
    
   
    for row in csv_data:
        month = int(row['month'])
        project_code = str(row['project'])
        hours = float(row['hours'])
        user_id = int(row['user_id'])

        dateM=datetime.date(2023,month,1)
        projectid = getattr(db.session.query(ModelProject).filter(ModelProject.project_code == project_code).first(),"id")

        searched_record=db.session.query(ModelMonthlyModifiedHours).filter(
                ModelMonthlyModifiedHours.project_id==projectid,
                ModelMonthlyModifiedHours.month==dateM,
                ModelMonthlyModifiedHours.user_id==user_id).first()
            
        if not searched_record:
            db_monthlyhour = ModelMonthlyModifiedHours(
                user_id = user_id,
                project_id = projectid,
                month = dateM,
                total_hours = hours
                )
        
            db.session.add(db_monthlyhour)
        else:
            searched_record.total_hours = hours


    db.session.commit()
    return {"message": "Import successful."}





