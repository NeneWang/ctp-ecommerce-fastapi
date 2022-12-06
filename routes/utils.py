from fastapi import  UploadFile, Path, HTTPException, status
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
    prefix="/utils",
    responses={404: {"description": "Not found"}},
    tags=["Utils"]
)

@router.get("/welcome", status_code=200)
async def getLogByID(id: str ):
    
    return {"Welcome": "Getting welcome message from: "+id}


@router.post("/{id}/upload/")
async def upload(id: str, file: UploadFile):
    """
    Uploads usign boto3 s3.
    """

    datet = datetime.datetime.now()
    datetimepre = datet.strftime("%m%d%Y%H%M%S")
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(S3_BUCKET_NAME)
    filedir = f'manual_uploads/{id}/{datetimepre+file.filename}'
    bucket.upload_fileobj(file.file, filedir)
    uploaded_file_url = f"s3://{S3_BUCKET_NAME}/{filedir}"

    
    return {"message": f"Successfully uploaded {file.filename}", "location": uploaded_file_url}


load_dotenv()

dotusername = os.getenv("USER")
@router.get('/getdot')
async def getDotUsername():
    return {"dotenv username": dotusername, "Unamked": os.getenv("UNMARKEDVARIABLE")}













