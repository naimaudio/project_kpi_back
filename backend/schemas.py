from typing import Optional, Union
from pydantic import BaseModel, validator
from datetime import date, datetime

class HoursUserBase(BaseModel):
    email: str
    username: str
    role: str

class FrontEndUser(HoursUserBase):
    id : int
    domain: Optional[str]
    role: str
    view: Optional[bool]
    date_entrance: Optional[date]
    status: str
    class Config:
            orm_mode = True

class HoursUser(HoursUserBase):
    password: str
    domain: Optional[str]
    role: Optional[str]
    view: Optional[bool]
    date_entrance: Optional[date]
    division: str
    status: str
    class Config:
            orm_mode = True



class Project (BaseModel):
    id: Optional[int]
    entity: str
    division: str
    sub_category: str
    classification: str 
    type: str
    project_name: str
    project_code: str
    project_manager: Optional[str]
    complexity: Optional[int]
    start_cap_date: Optional[date]
    end_cap_date: Optional[date]
    start_date: Optional[date]
    end_date: Optional[date]
    status: str

    class Config:
          orm_mode = True




class Record (BaseModel):
    date_rec: date
    user_id: int
    comment: Optional[str]
    
    class Config:
        orm_mode = True

class RecordProjects (BaseModel):
    project_id: int
    declared_hours: float
    domain: str

    @validator('declared_hours')
    def validate_half_1(cls,value):
        if not isinstance(value, int) and not (str(value).endswith('.5') or str(value).endswith('.0')):
              raise ValueError (f"Invalid value {value}. Only integers or half numbers allowed.")
        return value

    class Config:
        orm_mode = True

class Favorites (BaseModel):
    project_id: int
    user_id: int
       
    class Config:
        orm_mode = True

class BufferDailyRegister(BaseModel):
    
    user_id: int
    day_date: date
    project_id: int
    daily_hours: float

    @validator('daily_hours')
    def validate_half_2(cls,value):
        if not isinstance(value, int) and not (str(value).endswith('.5') or str(value).endswith('.0')):
              raise ValueError ("Invalid value. Only integers or half numbers allowed.")
        return value

class FrontendProjectPhase(BaseModel):
    project_phase: int
    start_date: date
    end_date: date
    
class ProjectPhase(FrontendProjectPhase):
    
    project_id: int
    end_date: date
    hours: float
    records: int


class MonthlyModifiedHours(BaseModel):
    user_id : int
    user_name: Optional[str]
    """List which has the following signature :
                    {"project_id": number,
                    "hours": number,
                    "domain": domain}
    """
    hours: list


class ProjectMonthlyInformation(BaseModel):
    project_id: Optional[int]
    month: int
    year: int
    forecast_hours: float
    capitalizable: Optional[bool]

class MonthlyReport(BaseModel):
    sync_date: Optional[datetime]
    closed: bool
    month: date
    