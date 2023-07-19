#Creating the SQLAlchemy parts
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#Make the database connection
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://kpi:projecthours@192.168.14.30:5432/project_kpi"

#Create an engine 
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#Create the SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Create the Base class
Base = declarative_base()





