from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class HoursUser(Base):
    __tablename__ = "hoursuser"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String,nullable=False) 
    email = Column(String, unique=True, nullable=False)
    password = Column(String,nullable=False)
    domain = Column(String)
    role = Column(String)
    view = Column(Boolean)
    date_entrance = Column(DateTime)

class Project(Base):
    __tablename__ = "project"

    id = Column(Integer,primary_key=True, index=True)
    entity = Column(String,nullable=False)
    division = Column(String,nullable=False)
    sub_category = Column(String,nullable=False)
    classification = Column(String,nullable=False)
    type = Column(String,nullable=False)
    project_name = Column(String,nullable=False)
    project_code = Column(String,nullable=False)
    project_manager = Column(String)
    current_phase = Column(String)
    complexity = Column(Integer)
    capitalization = Column(Boolean,nullable=False)
    

class Record(Base):
    __tablename__ = "record"

    user_id = Column(Integer,  ForeignKey("hoursuser.id"), primary_key = True)
    date_rec = Column(DateTime,nullable=False, primary_key = True)
    comment = Column(String)
   
class BufferDailyRegister(Base):
    __tablename__ = "buffer_daily_register"

    user_id = Column(Integer, ForeignKey("hoursuser.id"), primary_key = True)
    day_date = Column(DateTime,nullable=False, primary_key = True)
    project_id = Column(Integer, ForeignKey("project.id"), primary_key = True)
    daily_hours = Column(Integer,nullable=False)
    
    
class RecordProjects(Base):
    __tablename__ = "record_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,nullable=False)
    date_rec = Column(DateTime,nullable=False)
    project_id = Column(Integer, ForeignKey("project.id"))
    declared_hours = Column(Integer,nullable=False)
    modified_hours = Column(Integer)
    
    __table_args__ = (ForeignKeyConstraint(['user_id', 'date_rec'], ['record.user_id', 'record.date_rec']),
    )
    
    
  

class Favorites(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
        
    project_id = Column(Integer, ForeignKey("project.id"))
    user_id = Column(Integer, ForeignKey("hoursuser.id"))