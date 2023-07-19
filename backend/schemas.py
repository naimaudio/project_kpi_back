from typing import Optional
from pydantic import BaseModel
from datetime import date

class HoursUserBase(BaseModel):
    email: str
    username: str

class FrontEndUser(HoursUserBase):
    id : int
    domain: Optional[str]
    role: Optional[str]
    view: Optional[bool]
    date_entrance: Optional[date]
    
    class Config:
            orm_mode = True

class HoursUser(HoursUserBase):
    password: str
    domain: Optional[str]
    role: Optional[str]
    view: Optional[bool]
    date_entrance: Optional[date]
    
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
    current_phase: Optional[str]
    complexity: Optional[int] 
    capitalization: bool

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
    declared_hours: int

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
    daily_hours: int

