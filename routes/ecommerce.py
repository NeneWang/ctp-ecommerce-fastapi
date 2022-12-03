from fastapi import  UploadFile, Path
import models
from fastapi import APIRouter
from sqlalchemy.sql import exists, and_, or_
import boto3
from database import SessionLocal
from enum import Enum;
from pydantic import BaseModel
from typing import List
import datetime
from typing import Optional
import pandas as pd
from ecommerceEngine import RecommenderEngine, EDataframe
from slugify import slugify


PRODUCTS_FILE = "dist-data/products.csv"
INTERACTIONS_FILE = "dist-data/interactions.csv"
FILE_PRODUCT_MAPPINGS = "dist-data/product_mappings.csv"

ROW_PRODUCT_ID = "product_id"
ROW_SCORE = "score"

import os, json
from dotenv import load_dotenv
db = SessionLocal()


S3_BUCKET_NAME = 'myplatinumbucket'

def load_products():
    products_df = pd.read_csv(PRODUCTS_FILE)
    return products_df


df_products = load_products()


router = APIRouter(
    prefix="/ecommerce",
    responses={404: {"description": "Not found"}},
    tags=["Ecommerce"]
)



@router.get("/welcome", status_code=200)
async def getLogByID(id: str ):
    
    return {"Welcome": "Getting welcome message from: "+id}


@router.post('/create_sample')
async def createSample():
    """
    - [ ] Creates sample with items on the chart
    - [ ] You have multiple samples with different user ids
    """
    USERID_COMPUTER = "13"
    USERID_BYCICLE = "14"
    USERID_APPLIANCE = "15"

    interactions = []
    
    ID_LAPTOP = "1004739"
    ID_PHONE = "1306631"

    ID_BYCICLE = "12200053"
    ID_APPLIANCE ="3700600"

    interactions.append(
        models.Interaction(
        product_id=ID_LAPTOP,
        event_type=models.EEventTypes.VIEW.value,
        user_id=USERID_COMPUTER
    )
    )
    
    interactions.append(models.Interaction(
        product_id=ID_LAPTOP,
        event_type=models.EEventTypes.CART.value,
        user_id=USERID_COMPUTER
    ))

    
    interactions.append(models.Interaction(
        product_id=ID_LAPTOP,
        event_type=models.EEventTypes.PURCHASE.value,
        user_id=USERID_COMPUTER
    ))

    
    interactions.append(models.Interaction(
        product_id=ID_PHONE,
        event_type=models.EEventTypes.VIEW.value,
        user_id=USERID_COMPUTER
    ))

    
    interactions.append(models.Interaction(
        product_id=ID_PHONE,
        event_type=models.EEventTypes.VIEW.value,
        user_id=USERID_COMPUTER
    ))

    
    interactions.append(models.Interaction(
        product_id=ID_APPLIANCE,
        event_type=models.EEventTypes.VIEW.value,
        user_id=USERID_APPLIANCE
    ))

    interactions.append(models.Interaction(
        product_id=ID_APPLIANCE,
        event_type=models.EEventTypes.CART.value,
        user_id=USERID_APPLIANCE
    ))

    
    interactions.append(models.Interaction(
        product_id=ID_APPLIANCE,
        event_type=models.EEventTypes.PURCHASE.value,
        user_id=USERID_APPLIANCE
    ))

    
    interactions.append(models.Interaction(
        product_id=ID_BYCICLE,
        event_type=models.EEventTypes.VIEW.value,
        user_id=USERID_BYCICLE
    ))

    
    interactions.append(models.Interaction(
        product_id=ID_BYCICLE,
        event_type=models.EEventTypes.VIEW.value,
        user_id=USERID_BYCICLE
    ))

    
    interactions.append(models.Interaction(
        product_id=ID_BYCICLE,
        event_type=models.EEventTypes.CART.value,
        user_id=USERID_BYCICLE
    ))

    users = []

    users.append(
        models.User(
            user_id=USERID_COMPUTER,
        )
    )

    users.append(
        models.User(
            user_id=USERID_APPLIANCE,
        )
    )

    users.append(
        models.User(
            user_id=USERID_BYCICLE,
        )
    )

    for interaction in interactions:
        db.add(interaction)

    for user in users:
        db.add(user)



    db.commit()

@router.post('/populate_ecommerce/{nrows}')
def populateProducts(nrows:int = 1000000):
    df = pd.read_csv('data/2019-Oct.csv',nrows = nrows)
    ROW_CATEGORY_CODE = "category_code"
    ROW_CATEGORY_ID = "category_id"
    ROW_BRAND = "brand"
    ROW_NAME="product_name"
    ROW_PRODUCT_ID = "product_id"
    ROW_COUNT = "count"
    ROW_EVENT = "event_type"
    ROW_TIME = "event_time"
    ROW_PRICE = "price"
    ROW_SESSION = "user_session"
    ROW_IMG = "img_src"

    
    df[ROW_CATEGORY_CODE] = df[ROW_CATEGORY_CODE].astype(str)
    df[ROW_BRAND] = df[ROW_BRAND].astype(str) 

    def getImgSrc(product_id:str):
        return f"http://wngnelson.com/assets/img_src/oct1m/images/{product_id}.jpg"

    def create_name(dfrow):
        return returnSpaceForNan(dfrow[ROW_CATEGORY_CODE]) + " "+ returnSpaceForNan(dfrow[ROW_BRAND])

    def returnSpaceForNan(field):
        return field if field != "nan" else ""

    df[ROW_NAME] = df.apply(create_name, axis=1)
    gb_count = df.groupby(ROW_PRODUCT_ID)[ROW_NAME].agg(["count"])

    products = df.drop_duplicates(ROW_NAME)
    products = products.merge(gb_count,how="left" , on=ROW_PRODUCT_ID)
    products = products.sort_values(ROW_COUNT, ascending=False)
    columns_to_drop = [ROW_EVENT, ROW_TIME, ROW_SESSION]
    products = products.drop(columns=columns_to_drop)

    def loopProductsImages(df):
        sizedf = len(df)
        idx = 0
        
        for index, dfrow in df.iterrows():
            idx+=1
            model_product = models.Product(
                product_id = dfrow[ROW_PRODUCT_ID],
                category_id = dfrow[ROW_CATEGORY_ID],
                category_code = dfrow[ROW_CATEGORY_CODE],
                brand=dfrow[ROW_BRAND],
                price=dfrow[ROW_PRICE],
                product_name=dfrow[ROW_NAME],
                count=dfrow[ROW_COUNT],
                slug=slugify(dfrow[ROW_NAME]),
                priority = idx,
                img_src= getImgSrc(dfrow[ROW_PRODUCT_ID])
            )

            db.add(model_product)
    
    loopProductsImages(products)
    db.commit()

    return {"result" : "Success"}


@router.post('/populate_ecommerce_10m/{nrows}')
def populateProducts5m(nrows:int = 10000000):
    df = pd.read_csv('data/2019-Oct.csv',nrows = nrows)
    ROW_CATEGORY_CODE = "category_code"
    ROW_CATEGORY_ID = "category_id"
    ROW_BRAND = "brand"
    ROW_NAME="product_name"
    ROW_PRODUCT_ID = "product_id"
    ROW_COUNT = "count"
    ROW_EVENT = "event_type"
    ROW_TIME = "event_time"
    ROW_PRICE = "price"
    ROW_SESSION = "user_session"
    ROW_IMG = "img_src"

    
    df[ROW_CATEGORY_CODE] = df[ROW_CATEGORY_CODE].astype(str)
    df[ROW_BRAND] = df[ROW_BRAND].astype(str) 

    def getImgSrc(product_id:str):
        return f"http://wngnelson.com/assets/img_src/oct10m/images/{product_id}.jpg"

    def create_name(dfrow):
        return returnSpaceForNan(dfrow[ROW_CATEGORY_CODE]) + " "+ returnSpaceForNan(dfrow[ROW_BRAND])

    def returnSpaceForNan(field):
        return field if field != "nan" else ""

    df[ROW_NAME] = df.apply(create_name, axis=1)
    gb_count = df.groupby(ROW_PRODUCT_ID)[ROW_NAME].agg(["count"])

    products = df.drop_duplicates(ROW_NAME)
    products = products.merge(gb_count,how="left" , on=ROW_PRODUCT_ID)
    products = products.sort_values(ROW_COUNT, ascending=False)
    columns_to_drop = [ROW_EVENT, ROW_TIME, ROW_SESSION]
    products = products.drop(columns=columns_to_drop)

    def loopProductsImages(df):
        sizedf = len(df)
        idx = 0
        
        for index, dfrow in df.iterrows():
            idx+=1
            model_product = models.Product10m(
                product_id = dfrow[ROW_PRODUCT_ID],
                category_id = dfrow[ROW_CATEGORY_ID],
                category_code = dfrow[ROW_CATEGORY_CODE],
                brand=dfrow[ROW_BRAND],
                price=dfrow[ROW_PRICE],
                product_name=dfrow[ROW_NAME],
                count=dfrow[ROW_COUNT],
                slug=slugify(dfrow[ROW_NAME]),
                priority = idx,
                img_src= getImgSrc(dfrow[ROW_PRODUCT_ID])
            )

            db.add(model_product)
    
    loopProductsImages(products)
    db.commit()

    return {"result" : "Success"}


@router.post('/populate_ecommerce_all')
def populateProductsAll():
    df = pd.read_csv('data/products_oct.csv')
    ROW_CATEGORY_CODE = "category_code"
    ROW_CATEGORY_ID = "category_id"
    ROW_BRAND = "brand"
    ROW_NAME="product_name"
    ROW_PRODUCT_ID = "product_id"
    ROW_COUNT = "count"
    ROW_PRICE = "price"

    
    df[ROW_CATEGORY_CODE] = df[ROW_CATEGORY_CODE].astype(str)
    df[ROW_BRAND] = df[ROW_BRAND].astype(str) 

    def getImgSrc(product_id:str):
        return f"http://wngnelson.com/assets/img_src/oct/images/{product_id}.jpg"



    products = df.drop_duplicates(ROW_NAME)

    def loopProductsImages(df):
        idx = 0
        
        for index, dfrow in df.iterrows():
            idx+=1
            model_product = models.Product(
                product_id = dfrow[ROW_PRODUCT_ID],
                category_id = dfrow[ROW_CATEGORY_ID],
                category_code = dfrow[ROW_CATEGORY_CODE],
                brand=dfrow[ROW_BRAND],
                price=dfrow[ROW_PRICE],
                product_name=dfrow[ROW_NAME],
                count=dfrow[ROW_COUNT],
                slug=slugify(dfrow[ROW_NAME]),
                priority = idx,
                img_src= getImgSrc(dfrow[ROW_PRODUCT_ID])
            )

            db.add(model_product)
    
    loopProductsImages(products)
    db.commit()

    return {"result" : "Success"}


# Gets the interaction dataframe, user 13-> desktop, 14, 15
@router.get('/recommendations_merged/{session_id}')
async def getRecommendationsMerged(session_id: str):
    """
    - [ ] Get the dataframe based on the session id. (All interactions)
    - [ ] Convert that into an aggregation (based on algorihtms) (This should be handled by the engine)
    
    """

    # Todo this you need to get the query of all the items with certain id. THen you want to get into an aggregation
    allUserInteraction = db.query(models.Interaction).filter(models.Interaction.user_id == session_id).all()
    df_interacted_products = interactionLogsToDF(allUserInteraction=allUserInteraction)
       
    recommenderEngine = RecommenderEngine(df_interacted_products, INTERACTIONS_FILEIn=INTERACTIONS_FILE, FILE_PRODUCT_MAPPINGSIn= FILE_PRODUCT_MAPPINGS)
    
    recommenderEngine.populateRecommendation()
    prod_rec = recommenderEngine.getRecommendation()
    
    prod_rec[ROW_PRODUCT_ID] = prod_rec[ROW_PRODUCT_ID].astype(int)
    
    detailed_recommednation = prod_rec.merge(df_products, how="inner" , on=ROW_PRODUCT_ID)
    detailed_recommednation = detailed_recommednation.sort_values("mean")
    detailed_dict = detailed_recommednation.head(5).to_dict()
    print(detailed_dict)
    return(detailed_dict)

@router.get('/historial/{session_id}')
async def getHistorial(session_id: str):
    """
    - [x] Pass Simple Dataframe as json?
    - [ ] Also pass in (Left Merge) with the product information based on their id.
    """
    
    interacted_products = db.query(models.Interaction, models.Product).join( models.Product,
            models.Interaction.product_id == models.Product.product_id).filter(
                models.Interaction.user_id == session_id).all()
 
    return(interacted_products )
    
@router.get('/recommendations_products/{session_id}')
async def getRecommendationsProducts(session_id: str, limit: int=5):
    """
    - [x] Get the dataframe based on the session id. (All interactions)
    - [x] Returns ids of the recommendation as List[str]
    - [x] Get that as a function.
    - [x] Get user Interaction as df -> function
    """


    try:
        interacted_products = db.query(models.Interaction).filter(
                models.Interaction.user_id == session_id).all()
        df_interacted_products = interactionLogsToDF(allUserInteraction=interacted_products)
        
        unique_product_id = getRecommendedIdUsingDF(df_interacted_products=df_interacted_products, limit=5)
        
        print("Recommended list", unique_product_id)
        res_json = getProductsJSONFromList(unique_product_id)
        return(res_json )
    except Exception as e:
        return []


@router.get('/recommendations_detail_product/{product_id}')
async def getRecommendationsProductsFromDetail(product_id: str, limit: int=5):
    listInteract = []
    listInteract.append(
        models.Interaction(
            product_id=product_id,
            user_id=-1,
            event_type=models.EEventTypes.PURCHASE.value
        )
    )
    df_interacted_products = interactionLogsToDF(allUserInteraction=listInteract)
    
    unique_product_id = getRecommendedIdUsingDF(df_interacted_products=df_interacted_products, limit=5)
    
    print("Recommended list", unique_product_id)
    res_json = getProductsJSONFromList(unique_product_id)
    return(res_json )

def getProductsJSONFromList(product_id_list: List[str]) -> str:
    """
    [1, 2, 3] -> [Product(id: 1, ...), Product(id: 2, ...), Product(id: 3, ...)]
    """
    # product_id_list.append("44600062") # For testing if lists works
    product_id_list.append("2900536") # For testing if lists works
    # res = db.query(models.Product).filter(models.Product.product_id.in_(product_id_list)).all()
    # TODO Delete the following for normal
    res = db.query(models.Product).filter(models.Product.product_id.in_(product_id_list)).all()
    print("using get products form list")
    product_list = []
    
    for prod in res:
        product = models.ProductSchema(
            id = prod.id,
            guid = prod.guid,
            product_id=prod.product_id,
            category_id = prod.category_id,
            category_code=prod.category_code,
            brand=prod.brand,
            price=prod.price,
            product_name=prod.product_name,
            img_src=prod.img_src,
            slug=prod.slug,
            count=prod.count,
            priority=prod.priority

        )
        product_list.append(product)


    return [ ob.__dict__ for ob in product_list]

def interactionLogsToDF(allUserInteraction: List[models.Interaction]) -> pd.core.frame.DataFrame:
    productsRating  = dict()

    eventMappings = {
        models.EEventTypes.VIEW.value : 1,
        models.EEventTypes.CART.value : 3,
        models.EEventTypes.PURCHASE.value : 5,

    }

    for userInteraction in allUserInteraction:
        product_id = userInteraction.product_id
        event_type = userInteraction.event_type

        if product_id not in productsRating:
            productsRating[product_id] = 0
        
        try:
            productsRating[product_id] += eventMappings[event_type]
        except Exception as e:
            productsRating[product_id] += 0

    dictToVConvert = {}
    product_id_row = []
    product_score_row = []
    for key in productsRating:
        product_id_row.append(key)
        product_score_row.append(productsRating[key])

    dictToVConvert[ROW_PRODUCT_ID] = product_id_row
    dictToVConvert[ROW_SCORE] = product_score_row

    df_interacted_products = pd.DataFrame.from_dict(dictToVConvert)
    return df_interacted_products

def getRecommendedIdUsingDF(df_interacted_products: pd.core.frame.DataFrame, limit = -1) -> List[str]:
    
    recommenderEngine = RecommenderEngine(df_interacted_products, INTERACTIONS_FILEIn=INTERACTIONS_FILE, FILE_PRODUCT_MAPPINGSIn= FILE_PRODUCT_MAPPINGS)
    
    recommenderEngine.populateRecommendation()
    prod_rec = recommenderEngine.getRecommendation()
    
    
    prod_rec[ROW_PRODUCT_ID] = prod_rec[ROW_PRODUCT_ID].astype(int)
    detailed_recommednation = prod_rec.merge(df_products, how="inner" , on=ROW_PRODUCT_ID)
    detailed_recommednation = detailed_recommednation.sort_values("mean")
    
    detailed_recommednation[ROW_PRODUCT_ID] = detailed_recommednation[ROW_PRODUCT_ID].astype(str)
    unique_product_id = list(detailed_recommednation[ROW_PRODUCT_ID].unique())
    if(limit > 0):
        return unique_product_id[:limit]
    return unique_product_id


