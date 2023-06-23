from pydantic import BaseModel

class HoursUser(BaseModel):
    email: str
    username: str
    password: str
    id : int

    class Config:
            orm_mode = True


class Project (BaseModel):
     id: int
     division:  str
     classification: str
     type: bool
     name: str
     capitalization: bool
     entity: bool

     class Config:
          orm_mode = True


class Register (BaseModel):
    worked_hours: int
    project_id: int
    user_id: int
    
    class Config:
        orm_mode = True