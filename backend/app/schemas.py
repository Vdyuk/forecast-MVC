from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel
from datetime import datetime


ColorStatus = Literal["red", "yellow", "green", "in_work"]
FailureType = Literal["temperature", "flow", "complex"]
IncidentStatus = Literal["Новый", "В работе", "Отменен", "В ремонте", "Решен", "Статус не задан"]
HouseHealthStatus = Literal["Green", "Yellow", "Red"]
StatusIncidentType = Literal["Work", "Repair", "New", "Resolved"]


class DashboardMetrics(BaseModel):
	region_id: str
	region_name: str
	counts: dict
	period_days: int


class HouseListItem(BaseModel):
	house_id: str
	address: str
	region: str
	status: ColorStatus
	last_failure_date: Optional[str]
	incident_status: IncidentStatus
	unom: Optional[str] = None



class HouseDetail(BaseModel):
	house_id: str
	address: str
	simple_address: Optional[str] = None
	region: str
	status: ColorStatus
	incident_status: IncidentStatus
	last_failure_date: Optional[str]
	status_valid_until: Optional[str]
	status_reason: Optional[str]
	fias: Optional[str] = None
	unom: Optional[str] = None
	nreg: Optional[str] = None


class LLMQuestionRequest(BaseModel):
    question: str

class StatusHealthResponse(BaseModel):
    id: int
    id_house: int
    unom: int
    status_incident: Optional[str]
    house_health: Optional[str]
    created_at: datetime
    updated_at: datetime

class LublinoHousesResponse(BaseModel):
    id: int
    address: Optional[str]
    district: Optional[str]
    id_house: int
    n_fias: Optional[str]
    nreg: Optional[str]
    simple_address: Optional[str]
    unom: int
    created_at: datetime
    updated_at: datetime

class HouseWithStatusResponse(BaseModel):
    id_house: int
    unom: int
    status_incident: Optional[str]
    house_health: Optional[str]
    simple_address: Optional[str]
    address: Optional[str]
    district: Optional[str]