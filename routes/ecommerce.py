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
import pandas as pd
from ecommerceEngine import RecommenderEngine, EDataframe


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




# Gets the interaction dataframe, user 13-> desktop, 14, 15
@router.get('/rcommendations/{session_id}')
async def getRecommendations(session_id: str):
    """
    - [ ] Get the dataframe based on the session id. (All interactions)
    - [ ] Convert that into an aggregation (based on algorihtms) (This should be handled by the engine)
    
    """

    # Todo this you need to get the query of all the items with certain id. THen you want to get into an aggregation
    allUserInteraction = db.query(models.Interaction).filter(models.Interaction.user_id == session_id).all()
    print(allUserInteraction)

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
    # print(df_interacted_products.head())
    
    recommenderEngine = RecommenderEngine(df_interacted_products, INTERACTIONS_FILEIn=INTERACTIONS_FILE, FILE_PRODUCT_MAPPINGSIn= FILE_PRODUCT_MAPPINGS)
    
    recommenderEngine.populateRecommendation()
    prod_rec = recommenderEngine.getRecommendation()
    
    prod_rec[ROW_PRODUCT_ID] = prod_rec[ROW_PRODUCT_ID].astype(int)
    
    detailed_recommednation = prod_rec.merge(df_products, how="inner" , on=ROW_PRODUCT_ID)
    detailed_recommednation = detailed_recommednation.sort_values("mean")
    detailed_dict = detailed_recommednation.head(5).to_dict()
    print("detailed_dict")
    print(detailed_dict)
    return(json.dumps(detailed_dict))



