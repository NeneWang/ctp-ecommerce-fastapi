import uvicorn
from fastapi import FastAPI, Depends, File, UploadFile, Path, status, BackgroundTasks, HTTPException

# from http.client import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel, Field

import shortuuid
from database import SessionLocal, engine
import models
import os, json
from dotenv import load_dotenv
from routes import utils, ecommerce

from models import AuthDetails, AccountSchema
from auth import AuthHandler

import ast
import boto3
import awswrangler as wr
import pandas as pd


from pydantic import BaseModel
from sqlalchemy import Column, String, Float, Integer

from sqlalchemy.ext.declarative import declarative_base
from fastapi_crudrouter import SQLAlchemyCRUDRouter




load_dotenv()

dotusername = os.getenv("USER")

app = FastAPI()

db = SessionLocal()

Base = declarative_base()

def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


productRoutes = SQLAlchemyCRUDRouter(
    schema=models.ProductSchema,
    db_model= models.Product,
    db=get_db,
    prefix=models.Product.__tablename__

)

profileRoutes = SQLAlchemyCRUDRouter(
    schema=models.ProfileSchema,
    create_schema=models.ProfileCreate,
    update_schema=models.ProfileUpdate,
    db_model = models.Profile,
    db = get_db,
    prefix= models.Profile.__tablename__
)

interactionRoutes = SQLAlchemyCRUDRouter(
    schema=models.InteractionSchema,
    create_schema=models.InteractionCreate,
    db_model=models.Interaction,
    db = get_db,
    prefix=models.Interaction.__tablename__
)


app.include_router(profileRoutes)
app.include_router(productRoutes)
app.include_router(interactionRoutes)

app.include_router(utils.router)
app.include_router(ecommerce.router)



models.Base.metadata.create_all(bind=engine)

@app.get("/")
def index():
    return { "message": "hello world This is the Another update version"}

if __name__ == "__main__":
    uvicorn.run(app, port=8080, host='0.0.0.0')


auth_handler = AuthHandler()
users = []

@app.get('/product_slug/{slug}')
def getproductslug(slug: str):
    query_product = db.query(models.Product).filter(models.Product.slug == slug).first()
    return query_product

@app.get('/product_category/', tags=["Product"])
async def getDistinctCategory(limit:Optional[int] = 5):
    """
    - [x] Selects distinct category codes, and order by Priority
    """
    SQL_QUERY = f"SELECT category_code, count(*) as category_popularity from product WHERE category_code != 'nan' GROUP BY category_code ORDER BY category_popularity DESC LIMIT {limit}"
    rows = db.execute(SQL_QUERY).all()
    if(rows is None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query: {SQL_QUERY}",
        )
    return rows

@app.get('/product_category/{category_id}', tags=["Product"])
async def getProductsFromCategory(category_code:str, limit:Optional[int] = 5):
    rows = db.query(models.Product).filter(models.Product.category_code==category_code).limit(limit=limit).all()
    return rows

@app.get('/product_fromtopcategories/', tags=["Product"])
async def getDistinctCategory(limit:Optional[int] = 5):
    """
    - [x] Selects distinct category codes, and order by Priority
    - [x] Selects the most popular product from that category.
    """
    SQL_QUERY = f"SELECT gb.category_code, gb.category_popularity, p.count as product_popularity, p.* from (select category_code, COUNT(category_code) as category_popularity FROM product GROUP BY category_code ) gb LEFT JOIN ( select  product.* FROM product INNER JOIN ( SELECT category_code, MAX(count) as maxcount FROM product GROUP BY category_code ) mp ON mp.category_code = product.category_code AND mp.maxcount = product.count ORDER BY category_code ) p ON gb.category_code = p.category_code WHERE gb.category_code != 'nan' ORDER BY category_popularity DESC, count DESC LIMIT {limit}"
    rows = db.execute(SQL_QUERY).all()
    return rows

@app.post('/register', status_code=201)
def register(auth_details: AuthDetails):
    if any(x['username'] == auth_details.username for x in users):
        raise HTTPException(status_code=400, detail='Username is taken')
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    users.append({
        'username': auth_details.username,
        'password': hashed_password    
    })

    mdAccount = models.Account( 
        username= auth_details.username,
        password= hashed_password 
    )
    
    db.add(mdAccount)
    db.commit()
    return




@app.post('/login')
def login(auth_details: AuthDetails):
    userAccount = None
    
    userAccount = db.query(models.Account).filter(models.Account.username == auth_details.username).first()
    if(userAccount is None):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    
    if(userAccount is None) or (not auth_handler.verify_password(auth_details.password, userAccount.password)):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')

    token = auth_handler.encode_token(userAccount.username)
    return { 'token': token }


@app.get('/unprotected')
def unprotected():
    return { 'hello': 'world' }


@app.get('/protected')
def protected(username=Depends(auth_handler.auth_wrapper)):
    return { 'name': username }