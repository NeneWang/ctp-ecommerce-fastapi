from fastapi import  UploadFile, Path
import models
from fastapi import APIRouter
from sqlalchemy.sql import exists, and_, or_
import boto3
from database import SessionLocal
from enum import Enum;
from pydantic import BaseModel
import datetime
from typing import Optional

import os, json
from dotenv import load_dotenv



S3_BUCKET_NAME = 'myplatinumbucket'

router = APIRouter(
    prefix="/ecommerce",
    responses={404: {"description": "Not found"}},
    tags=["Ecommerce"]
)



@router.get("/welcome", status_code=200)
async def getLogByID(id: str ):
    
    return {"Welcome": "Getting welcome message from: "+id}

# Gets the interaction dataframe
@router.get('/rcommendations/{session_id}')
async def getRecommendations(session_id: str):
    """
    - [ ] Get the dataframe based on the session id. (All interactions)
    - [ ] Convert that into an aggregation (based on algorihtms) (This should be handled by the engine)
    
    """

    # Todo this you need to get the query of all the items with certain id. THen you want to get into an aggregation


    pass



