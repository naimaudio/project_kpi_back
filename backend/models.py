from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, ForeignKeyConstraint, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class HoursUser(Base):
    __tablename__ = "hoursuser"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String,nullable=False) 
    email = Column(String, unique=True, nullable=False)
    domain = Column(String, nullable=False)
    role = Column(String, nullable=False)
    view = Column(Boolean, nullable=False)
    date_entrance = Column(DateTime, nullable=False)

class Project(Base):
    __tablename__ = "project"

    id = Column(Integer,primary_key=True, index=True)
    entity = Column(String,nullable=False)
    division = Column(String,nullable=False)
    sub_category = Column(String,nullable=False)
    classification = Column(String,nullable=False)
    type = Column(String,nullable=False)
    project_name = Column(String,nullable=False)
    project_code = Column(String,nullable=False,unique=True)
    project_manager = Column(String)
    complexity = Column(Integer)
    start_cap_date = Column(DateTime, nullable=False)
    end_cap_date = Column(DateTime, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    

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
    daily_hours = Column(Numeric(precision=3,scale=1),nullable=False)
    
    
class RecordProjects(Base):
    __tablename__ = "record_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,nullable=False)
    date_rec = Column(DateTime,nullable=False)
    project_id = Column(Integer, ForeignKey("project.id"))
    declared_hours = Column(Numeric(precision=3,scale=1),nullable=False)
    
    
    __table_args__ = (ForeignKeyConstraint(['user_id', 'date_rec'], ['record.user_id', 'record.date_rec']),
    )
    
class ProjectPhase(Base):
    __tablename__ = "project_phases"

    project_id = Column(Integer, ForeignKey("project.id"), primary_key = True)
    project_phase = Column(Integer,nullable=False, primary_key = True)
    start_date = Column(DateTime,nullable=False)
    end_date = Column(DateTime,nullable=False)
    hours = Column(Integer)


class MonthlyModifiedHours(Base):
    __tablename__ = "monthly_modified_hours"
    
    user_id = Column(Integer, ForeignKey("hoursuser.id"), primary_key = True)
    project_id = Column(Integer, ForeignKey("project.id"), primary_key = True)
    month = Column(DateTime,nullable=False, primary_key = True)
    total_hours = Column(Numeric(precision=3,scale=1))

class MonthlyForecast(Base):
    __tablename__ = "monthly_forecast"
    
    project_id = Column(Integer, ForeignKey("project.id"), primary_key = True)
    month = Column(DateTime,nullable=False, primary_key = True)
    hours = Column(Numeric(precision=3,scale=1))
  

class Favorites(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
        
    project_id = Column(Integer, ForeignKey("project.id"))
    user_id = Column(Integer, ForeignKey("hoursuser.id"))