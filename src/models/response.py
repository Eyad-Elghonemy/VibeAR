from pydantic import BaseModel
from typing import List, Dict


class PredictionObject(BaseModel):
    
    text: str
    predictions: Dict
    
    
class PredictionObjects(BaseModel):
    
    predictions: List[PredictionObject]
    
    
    
class StatusObject(BaseModel):
    
    status: str
    timestamp: str
    classes: List[str]
    evaluation: Dict