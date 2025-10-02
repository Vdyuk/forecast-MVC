from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class StatusHealth(Base):
    __tablename__ = "status_houses"
    
    id_house = Column(BigInteger, primary_key=True, nullable=False, index=True)
    unom = Column(BigInteger, nullable=False, index=True)
    status_incident = Column(String(50), nullable=True)  # Work, Repair, Null, New, Resolved
    house_health = Column(Text, nullable=True)  # Green, Yellow, Red

class LublinoHousesId(Base):
    __tablename__ = "lublino_houses_id"
    
    unom = Column(BigInteger, primary_key=True, nullable=False, index=True)
    n_fias = Column(String(50), nullable=True)
    id_house = Column(BigInteger, nullable=False, index=True)
    nreg = Column(String(50), nullable=True)
    simple_address = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    district = Column(String(100), nullable=True)

class ModelRelearn(Base):
    __tablename__ = "model_relearn"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    model_name = Column(String(100), nullable=False)
    status_relearn = Column(String(50), nullable=False)
