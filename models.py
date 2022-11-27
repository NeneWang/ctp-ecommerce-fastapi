
from email.policy import default
from sqlalchemy import PrimaryKeyConstraint, String,Boolean,Integer,Column, Table,Text, DateTime, ARRAY, Identity, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import datetime, uuid
import shortuuid
from sqlalchemy.ext.declarative import declarative_base
from database import Base
from sqlalchemy import func

func.systime = lambda: str(datetime.datetime.utcnow())
func.autoid = lambda: str(shortuuid.uuid())

import json
Base = declarative_base()

from pydantic import BaseModel
from typing import List, Optional

class Organization(Base):
    __tablename__ = 'organization'

    bucketJson = {   "activity": {     "description": "Bucket that maps into different activity categories",     "buckets": {       "Create": ["Create", "New-Mailbox"],       "Access": ["FilePreviewed"],       "Update": ["Update"],       "Delete": ["SoftDelete", "MoveToDeletedItems", "HardDelete"],       "Organize": ["FolderCreated"],       "Admin": ["UserLoggedIn"],       "Browse": ["SearchQueryPerformed"],       "None": ["FileSyncUploadedFull"]     }   },   "application_category": {     "description": "Categorization of Applications",     "buckets": {       "Storage": [         "OneDrive",         "SecurityComplianceCenter",         "AzureActiveDirectory",         "SoftDelete"       ],       "Communication": ["Create", "Exchange", "Quarantine", "MicrosoftTeams"],       "ProjectManagement": ["SharePoint"],       "Login": ["Browser", "Mobile Apps and Desktop clients"]     }   },   "operation": {     "description": "Bucket that maps into different activity categories",     "buckets": {       "Create": "Create",       "MipLabel": "Admin"     }   },   "application_type": {     "description":"Bucket that maps Application Mapper",     "buckets": {       "Exchange":"Communication"     }   } } 
    
    id = Column(Integer, primary_key=True, autoincrement=True , index=True)
    guid = Column(String(255), nullable=True, server_default = func.gen_random_uuid()) 
    name = Column(String(255), nullable=True, server_default="")
    email = Column(String(255), nullable=True, server_default="")
    tenant_id = Column(String(255), nullable=True, server_default="")
    tenant_secret = Column(String(255), nullable=True, server_default="")
    tenant_domain=Column(String(255), nullable=True, server_default="")
    mapping_instruction=Column(Text, nullable=True, server_default='{   "activity": {     "description": "Bucket that maps into different activity categories",     "buckets": {       "Create": ["Create", "New-Mailbox"],       "Access": ["FilePreviewed"],       "Update": ["Update"],       "Delete": ["SoftDelete", "MoveToDeletedItems", "HardDelete"],       "Organize": ["FolderCreated"],       "Admin": ["UserLoggedIn"],       "Browse": ["SearchQueryPerformed"],       "None": ["FileSyncUploadedFull"]     }   },   "application": {     "description": "Categorization of Applications",     "buckets": {       "Storage": [         "OneDrive",         "SecurityComplianceCenter",         "AzureActiveDirectory",         "SoftDelete"       ],       "Communication": ["Create", "Exchange", "Quarantine", "MicrosoftTeams"],       "ProjectManagement": ["SharePoint"],       "Login": ["Browser", "Mobile Apps and Desktop clients"]     }   },   "operation": {     "description": "Bucket that maps into different activity categories",     "buckets": {       "Create": "Create",       "MipLabel": "Admin"     }   } } ')
    mapping_buckets=Column(Text, nullable=True, server_default=json.dumps(bucketJson))
    
    employees = relationship("Employee", back_populates="organization", lazy="joined")
    profiles = relationship("Profile", back_populates="organization", lazy="joined")
    

    created_time=Column(DateTime, nullable=True, server_default=func.now())
    update_time=Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"Account name {self.name}"

class Employee(Base):
    __tablename__="employee"
    id=Column(Integer, primary_key = True, autoincrement=True, index=True)
    guid = Column(String(255), nullable=True, server_default = func.gen_random_uuid())
    first_name = Column(String(), nullable=True, server_default="")
    last_name = Column(String(), nullable=True, server_default="")
    middle_name = Column(String(), nullable=True, server_default="")
    active = Column(Boolean(), nullable=True)
    timezone = Column(String(), nullable=True, server_default="US/Eastern")
    email = Column(String(255), nullable=True, server_default="")
    work_days = Column(ARRAY(Integer), nullable=True)
    work_hours_start = Column(ARRAY(Integer), nullable=True)
    work_hours_end = Column(ARRAY(Integer), nullable=True)
    supervisor_id = Column(Integer, nullable=True)
    name=Column(String, nullable=True)
    id_365 = Column(String, nullable=True, server_default="nelson@o365.devcooks.com")

    profile_id = Column(Integer, ForeignKey("profile.id") ,nullable=True)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=True)
    time_slot_split = Column(Integer, nullable=True, default=1)
    escape_dates = Column(ARRAY(String), nullable=True)


    # Relationships
    organization = relationship("Organization", back_populates="employees", lazy="subquery")
    profile = relationship("Profile", back_populates="employee", lazy="subquery")
    
class Profile(Base):
    __tablename__="profile"
    bucketJson = {"activity": { "description": "Bucket that maps into different activity categories",        "buckets": {   "Create": ["Create"],   "Access": ["FilePreviewed"],   "Update": ["Updatee"],   "Delete": ["SoftDelete", "MoveToDeletedItems", "HardDelete"], "Organize": ["FolderCreated"], "Admin": ["UserLoggedIn"], "Browse": ["SearchQueryPerformed"], "None": ["FileSyncUploadedFull"],        },    },    "application": {        "description": "Categorization of Applications",        "buckets": { "Storage": [     "OneDrive",     "SecurityComplianceCenter",     "AzureActiveDirectory",     "SoftDelete", ], "Communication": ["Create", "Exchange", "Quarantine", "MicrosoftTeams"], "ProjectManagement": ["SharePoint"], "Login": ["Browser", "Mobile Apps and Desktop clients"],        },    },}
    id=Column(Integer, primary_key = True, autoincrement=True)
    guid = Column(String(255), nullable=True, server_default = func.gen_random_uuid())
    name = Column(String(255), nullable=True, server_default="") 
    mapping_instruction = Column(Text, nullable=True, server_default=json.dumps(bucketJson))
    organization_id=Column(Integer, ForeignKey("organization.id"), nullable=True) 

    organization = relationship("Organization", back_populates="profiles")
    employee = relationship("Employee", back_populates="profile")


from enum import Enum
class EEventTypes(Enum):
    VIEW = "view"
    CART = "cart"
    PURCHASE = "purchase"

class Interaction(Base):
    """
    Only for storing User Session
    """
    
    __tablename__="interaction"
    id = Column(Integer, primary_key=True, autoincrement=True)
    guid = Column(String(255), nullable=True, server_default = func.gen_random_uuid())
    product_id = Column(String(255), nullable=True, server_default = "")
    user_id = Column(String(255), nullable=True, server_default = "")
    event_type = Column(String, nullable=True, server_default=EEventTypes.VIEW.value )
    
class Account(Base):
    __tablename__ = "account"
    id=Column(Integer, primary_key = True, autoincrement=True, index=True)
    guid = Column(String(255), nullable=True, server_default = func.gen_random_uuid())
    username = Column(String)
    password = Column(String)

class ProfileCreate(BaseModel):
    name: Optional[str]
    organization_id:int

class ProfileUpdate(BaseModel):
    name: Optional[str]
    mapping_instruction:Optional[str]

class ProfileSchema(ProfileUpdate):
    id: Optional[int]
    guid:Optional[str]
    organization_id:int

    class Config:
        orm_mode = True



class InteractionCreate(BaseModel):
    product_id: str
    event_type:str
    user_id: str

class InteractionSchema(InteractionCreate):
    id: int
    guid: str

class AccountSchema(BaseModel):
    username:str
    password:str



class AuthDetails(BaseModel):
    username: str
    password: str
