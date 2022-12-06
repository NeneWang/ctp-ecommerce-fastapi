import uvicorn
from fastapi import FastAPI, Depends, status, HTTPException

# from http.client import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from database import SessionLocal, engine
import models
import os
from dotenv import load_dotenv
from routes import utils, ecommerce

from models import AuthDetails, AccountSchema
from auth import AuthHandler

import ast
import boto3
import pandas as pd


from pydantic import BaseModel
from sqlalchemy import Column, String, Float, Integer

from sqlalchemy.ext.declarative import declarative_base
from fastapi_crudrouter import SQLAlchemyCRUDRouter

from slugify import slugify
from typing import List


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

bannerRoutes = SQLAlchemyCRUDRouter(
    schema=models.BannerSchema,
    db_model=models.Banner,
    db=get_db,
    prefix=models.Banner.__tablename__
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
app.include_router(bannerRoutes)
app.include_router(interactionRoutes)

app.include_router(utils.router)
app.include_router(ecommerce.router)



models.Base.metadata.create_all(bind=engine)

@app.get("/")
def index():
    return { "message": "Version with Reordering"}




@app.get('/product_slug/{slug}')
def getproductslug(slug: str):
    query_product = db.query(models.Product).filter(models.Product.slug == slug).first()
    return query_product

@app.get('/product_category/', tags=["Product"])
async def getDistinctCategory(limit:Optional[int] = 5):
    """
    - [x] Selects distinct category codes, and order by Priority
    - [ ] Include slug to results object list
    """
    SQL_QUERY = f"SELECT category_code, count(*) as category_popularity from product WHERE category_code != 'nan' GROUP BY category_code ORDER BY category_popularity DESC LIMIT {limit}"
    rows = db.execute(SQL_QUERY).all()
    if(rows is None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query: {SQL_QUERY}",
        )

    formatted_response = []
    for row in rows:
        new_row = {}
        new_row['slug'] = slugify(row.category_code)
        new_row["category_popularity"] = row.category_popularity
        new_row["category_code"] = row.category_code
        formatted_response.append(new_row)
        
    return formatted_response

@app.get('/product_category/{category_code}', tags=["Product"])
async def getProductsFromCategory(category_code:str, limit:Optional[int] = 5):
    rows = db.query(models.Product).filter(models.Product.category_code==category_code).limit(limit=limit).all()
    return rows

@app.get('/product_category_from_slug/{category_slug}', tags=["Product"])
async def getProductsFromCategory(category_slug:str, limit:Optional[int] = 5):
    rows = db.query(models.Product, models.Banner).join(
        models.Banner, models.Product.category_code == models.Banner.category_code).filter(
            models.Banner.slug==category_slug).limit(limit=limit).all()
    return rows

@app.get('/product_fromtopcategories/', tags=["Ecommerce"])
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



auth_handler = AuthHandler()
users = []

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




@app.get('/favored/{category}', tags=["Banner"])
def getFavoredBannerByCategory(category: str):
    """
    - [ ] Get the most popular (effective) Banner from that cateogry
    - [ ] TODO: Create another API so that is more like a probability that will chose the first one if appropriate.
    """
    query_banner = db.query(models.Banner).filter(models.Banner.category_code == category).first()
    
    # What I don't get is why it doesn't create
    return query_banner

@app.post('/create_banners', tags=["Banner"])
def createSampleBanners():
    """
    Create Sample BAnners based on existent images. if repeated the image url will be adding a 0 to it's count
    e.g. [electronics, electronics] -> [electronics, electronics_1]
    """

    product_banners = ["apparel.shoes", "appliances.environment.air_heater", "appliances.environment.vacuum", "appliances.kitchen.oven",
    "appliances.kitchen.refrigerators", "appliances.kitchen.washer", "auto.accessories.alarm", "computers.desktop",
    "computers.notebook", "computers.notebook", "electronics.audio.headphone", "electronics.clocks",
    "electronics.smartphone", "electronics.tablet", "electronics.video.tv", "electronics.video.tv"]

    
    BANNERS_BNP = [""]
    list_banners = []
    # Creates dynamic banners

    URL_BASE = "http://wngnelson.com/assets/img_src/banners/"

    def getPostfix(count: int):
        """
        Get the postfix e.g. 1 -> "" 2 -> "_1"
        """
        if(count > 1):
            index_id = count - 1;
            return f"_{index_id}"
        return ""

    def create_product_url(category_code: str, count: int):
        """
        Gets Product URL
        """
        # If the count is >1: 2-> 1
        return URL_BASE + category_code + getPostfix(count=count) + ".png"


    def populateBannerList(product_banners: List[str], list_banners: List[models.CreateBannerSchema]):
        count_product_list = {} #string: int
        for product_category in product_banners:
            if product_category not in count_product_list:
                count_product_list[product_category] = 0    
            count_product_list[product_category] += 1

            product_link = create_product_url(category_code=product_category, count=count_product_list[product_category])
            list_banners.append(
                models.CreateBannerSchema(
                    category_code=product_category,
                    slug=slugify(product_category),
                    description="",
                    popularity_score=0,
                    is_dynamic=False,
                    img_src=product_link,

                )
            )

    def publishBannerList(list_banners: List[models.CreateBannerSchema]):
        for banner in list_banners:
            bannerModel = models.Banner(
                category_code = banner.category_code,
                img_src = banner.img_src,
                description = banner.description,
                popularity_score = banner.popularity_score,
                is_dynamic=banner.is_dynamic,
                slug=banner.slug
            )
            db.add(bannerModel)
            db.commit()

    populateBannerList(product_banners = product_banners, list_banners=list_banners)
    publishBannerList(list_banners=list_banners)
    return list_banners


@app.post('/create_model_a', tags=["Util"])
def createModelA():
    """
    Reads from csv and uploads all
    """

if __name__ == "__main__":
    uvicorn.run(app, port=8080, host='0.0.0.0')

