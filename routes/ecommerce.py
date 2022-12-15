from fastapi import  UploadFile, Path, HTTPException, status
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
from utils import raiseExceptionIfRowIsNone
import psycopg2
from sqlalchemy import create_engine
from utils import rollBack


PRODUCTS_FILE = "dist-data/products.csv"
INTERACTIONS_FILE = "dist-data/interactions.csv"

# TODO: Uncomment this on production
# PRODUCTS_FILE = "data/products_oct.csv"
INTERACTIONS_FILE = "data/oct_interactions.csv"
INTERACTIONS_FILE_CAPPED = "data/oct_interactions_capped.csv"
FILE_PRODUCT_MAPPINGS = "dist-data/product_mappings.csv"

ROW_SCORE = "score"
ROW_CATEGORY_CODE = "category_code"
ROW_CATEGORY_ID = "category_id"
ROW_BRAND = "brand"
ROW_NAME="product_name"
ROW_PRODUCT_ID = "product_id"
ROW_USER="user"
ROW_COUNT = "count"
ROW_EVENT = "event_type"
ROW_TIME = "event_time"
ROW_PRICE = "price"
ROW_SESSION = "user_session"
ROW_IMG = "img_src"

import os, json
from dotenv import load_dotenv
db = SessionLocal()


S3_BUCKET_NAME = 'myplatinumbucket'

def load_products():
    alchemyEngine   = create_engine('postgresql://postgres:ctpcommerce27@ecommerce.caxc6cq8wvo5.us-east-1.rds.amazonaws.com/postgres', pool_recycle=3600);
        
    dbConnection    = alchemyEngine.connect();
    products_df = pd.read_sql('select * from "product"', dbConnection);
    products_df['product_id'] = products_df['product_id'].astype(int)
    return products_df


df_products = load_products()


router = APIRouter(
    prefix="/ecommerce",
    responses={404: {"description": "Not found"}},
    tags=["Ecommerce"]
)


@router.post('/create_model_a', tags=["Util"])
def createModelA():
    """
    Reads from csv and uploads intearctions in table: model=models.InteractionModelB
    """
    return populateInteractions(INTERACTIONS_FILE, model=models.InteractionModelA)

@router.post('/create_model_b', tags=["Util"])
def createModelA():
    """
    Reads from csv that is capped on 10 in table: model=models.InteractionModelB
    """
    return populateInteractions(INTERACTIONS_FILE_CAPPED, model=models.InteractionModelB)


def populateInteractions(intearaction_file, model):
    df = pd.read_csv(intearaction_file)
    df[ROW_PRODUCT_ID] = df[ROW_PRODUCT_ID].astype(str)
    df[ROW_USER] = df[ROW_USER].astype(str)
    df[ROW_SCORE] = df[ROW_SCORE].astype(int)
    count = 0
    for index, dfrow in df.iterrows():
        count+=1
        model_product = model(
            product_id = dfrow[ROW_PRODUCT_ID],
            user= dfrow[ROW_USER],
            score = dfrow[ROW_SCORE],
        )
        db.add(model_product)
    db.commit()
    return {"Created", count}

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



def sorted_legal_category(legal_category_codes: List[str], products: List[models.ProductSchema]) -> dict:
    dict_count_category = {} # category_code:str -> counts: int

    for product in products:
        category_code = product.category_code
        if category_code not in dict_count_category:
            dict_count_category[category_code] = 0
        dict_count_category[category_code] +=1
        
    list_categories_attained = dict_count_category.keys()
    list_categories_attained_that_are_legal = filter(lambda category: category in legal_category_codes, list_categories_attained)

    list_legal_count_dict = {key: dict_count_category[key]  for key in list_categories_attained_that_are_legal  }
    list_legal_sorted_d = sorted(list_legal_count_dict.items(), key=lambda x: x[1])
    list_legal_sorted = [ x[0] for x in list_legal_sorted_d]
    return list_legal_sorted

@router.get('/banner_categories', tags=["Banner"])
def getAvailableBannerCategories(limit:Optional[int]=20) -> List[str]:
    """
    - [x] Gets available categories based on the banners registered on the database
    - [x] Dict are sorted
    - [x] Parameter for limiting output.
    """
    SQL_QUERY = "SELECT category_code FROM banner  WHERE category_code != 'nan' GROUP BY category_code"
    rows = db.execute(SQL_QUERY).all()
    raiseExceptionIfRowIsNone(rows = rows, SQL_QUERY=SQL_QUERY)
    list_available_categories = [ category.category_code for category  in rows ]
    limit = get_tamed_limit(listforlimit=list_available_categories, original_limit=limit)
    return list_available_categories[:limit]

def get_tamed_limit(original_limit: int, listforlimit: List) -> int : 
    """
    Safeguard for if theuser chooses a limit larger than the list we want.
    e.g. original limit: 4, list size: 2 -> 2

    """
    lenlistlimit = len(listforlimit)
    if original_limit > lenlistlimit:
        return lenlistlimit
    return original_limit


def banners_from_list(category_code_list: List[str]) -> List[models.Banner]:
    SQL_QUERY = "SELECT * FROM banner WHERE category_code IN ("
    categories_query:str = ""
    category_code_list = [f"'{x}'" for x in category_code_list]
    category_code_list = ', '.join(category_code_list)
    SQL_QUERY += category_code_list
    SQL_QUERY += ")"
    rows = db.execute(SQL_QUERY).all()
    raiseExceptionIfRowIsNone(rows= rows, SQL_QUERY=SQL_QUERY)

    
    return rows


@router.get('/recommended_category/{session_id}', tags=["Ecommerce"])
async def getTopRecommendedBanner(session_id: str, limit: Optional[int] = 2, append_if_default:Optional[bool] =True)->List[models.Banner]:
    """
    - [x] Gets the top recommended Banner based on id [Only from banners that are possible to get.]
    - By default the top 2.
    """

    legal_codes:List[str] = getAvailableBannerCategories()


    
    try:
        interacted_products = db.query(models.Interaction).filter(
                models.Interaction.user_id == session_id).all()
        df_interacted_products = interactionLogsToDF(allUserInteraction=interacted_products)
        
        unique_product_id = getRecommendedIdUsingDF(df_interacted_products=df_interacted_products, limit=5)
        
        res_json:List[models.ProductSchema] = getProductsJSONFromList(unique_product_id)
        list_legal_count_dict:List[str] = sorted_legal_category(legal_category_codes=legal_codes, products=res_json)

        if(append_if_default):
            list_legal_count_dict.extend(legal_codes)
            list_legal_count_dict = list(dict.fromkeys(list_legal_count_dict))
        
        tamed_limit = get_tamed_limit(listforlimit= list_legal_count_dict, original_limit=limit)
        list_legal_count_dict = list_legal_count_dict[:tamed_limit]
        return banners_from_list(list_legal_count_dict)

    except Exception as e:
        
        tamed_limit = get_tamed_limit(listforlimit= legal_codes, original_limit=limit)
        returning_categories = legal_codes[:tamed_limit]
        return banners_from_list(returning_categories)


# Gets the interaction dataframe, user 13-> desktop, 14, 15
@router.get('/recommendations_merged/{session_id}')
async def getRecommendationsMerged(session_id: str) -> List[models.Product]:
    """
    - [x] Get the dataframe based on the session id. (All interactions)
    - [x] Convert that into an aggregation (based on algorihtms) (This should be handled by the engine)
    
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
    return(detailed_dict)


@router.get('/rollback')
def rollBack():
    """
    If the server suddenly stops, run this
    """
    rollBack(db=db)

@router.get('/historial/{session_id}')
async def getHistorial(session_id: str):
    """
    - [x] Pass Simple Dataframe as json?
    - [x] Also pass in (Left Merge) with the product information based on their id.
    - [x] Sorted by creation time
    """
    db.rollback()
    
    interacted_products = db.query(models.Interaction, models.Product).join( models.Product,
            models.Interaction.product_id == models.Product.product_id).filter(
                models.Interaction.user_id == session_id).order_by(models.Interaction.created_time).all()
 
    return(interacted_products )
    
@router.delete('/historial/{session_id}')
async def deleteHistorialFrom(session_id: str):
    """
    - [ ] Deletes the historial from all interactions where session id is ...
    """
    db.query(models.Interaction).filter(models.Interaction.user_id == session_id ).delete()
    db.commit()
    return {"Message": f"Successfully deleted all interactions from {session_id}"}

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
    try:
        df_interacted_products = interactionLogsToDF(allUserInteraction=listInteract)
    
        unique_product_id = getRecommendedIdUsingDF(df_interacted_products=df_interacted_products, limit=5)
        
        res_json = getProductsJSONFromList(unique_product_id)
        return res_json 
    except Exception as e:
        return []

def getProductsJSONFromList(product_id_list: List[str]) -> List[models.ProductSchema]:
    """
    [1, 2, 3] -> [Product(id: 1, ...), Product(id: 2, ...), Product(id: 3, ...)]
    """
    # product_id_list.append("44600062") # For testing if lists works
    product_id_list.append("2900536") # For testing if lists works
    # res = db.query(models.Product).filter(models.Product.product_id.in_(product_id_list)).all()
    # TODO Delete the following for normal
    res = db.query(models.Product).filter(models.Product.product_id.in_(product_id_list)).all()
    print("using get products form list")
    product_list: List[models.Product] = []
    
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


    return product_list

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


