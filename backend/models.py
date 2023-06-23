from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class HoursUser(Base):
    __tablename__ = "hoursuser"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True) 
    email = Column(String, unique=True, index=True)
    password = Column(String)

class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    division = Column(String, index=True)
    classification = Column(String, index=True)
    type = Column(Boolean)
    name = Column(String, index=True)
    capitalization = Column(Boolean)
    entity = Column(Boolean)

class Register(Base):
    __tablename__ = "register"

    id = Column(Integer, primary_key=True, index=True)
    worked_hours = Column(Integer, index=True)
    
    project_id = Column(Integer, ForeignKey("project.id"))
    user_id = Column(Integer, ForeignKey("hoursuser.id"))
    
    project = relationship("Project")
    hoursuser = relationship("HoursUser")
