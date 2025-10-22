from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

class CompanyRole(str, Enum):
    admin = "admin"
    user = "user"

class CompanyBase(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone: str
    role: CompanyRole = CompanyRole.user   # 👈 default is "user"

class CompanyCreate(CompanyBase):
    password: str

class Company(CompanyBase):
    id: int
    class Config:
        from_attributes = True

class AgentBase(BaseModel):
    name: str

class AgentCreate(AgentBase):
    company_id: int
    campaign_agents_id: int
    campaign_id: int

class Agent(AgentBase):
    id: int
    company_id: int
    campaign_agents_id: int
    campaign_id: int
    class Config:
        from_attributes = True

class CampaignCreate1(BaseModel):
    name: str
    email: EmailStr
    status: str = "Paused"  # optional

class CampaignCreate2(BaseModel):
    id: int
    name: str
    email: EmailStr
    status: str = "Paused"
    created_at: datetime

    # Computed fields
    total_customers: int
    interested_customers: int
    not_interested_customers: int
    maybe_customers: int

    class Config:
        orm_mode = True

class CampaignBase(BaseModel):
    name: str
    # email: EmailStr
    # start_date: datetime

class CampaignCreate(CampaignBase):
    company_id: int
    campaign_id: int
    agents: List[str]   # 👈 names of agents

class Campaign(CampaignBase):
    id: int
    created_at: datetime
    company_id: int
    agents: List[Agent] = []   # nested
    campaign_id: int
    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    name: str
    phone: str
    conversation: Optional[str] = None

class CustomerCreate(CustomerBase):
    campaign_id: int
    campaign_agent_id: int

class Customer(CustomerBase):
    id: int
    status: str
    campaign_id: int
    campaign_agent_id: int
    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    phone_number: str
    agent_id: str
    conversation_id: str
    language: Optional[str]
    messages: List[dict]

class CallPayload(BaseModel):
    id: int          # campaign or other entity id
    type: str        # "campaign" or other

from typing import List, Optional
from pydantic import BaseModel

class CustomerOut(BaseModel):
    id: int
    name: str
    phone: str
    status: str
    conversation: Optional[str]

    class Config:
        orm_mode = True

class AgentOut(BaseModel):
    id: int
    name: str
    # optionally include customers
    customers: List[CustomerOut] = []

    class Config:
        orm_mode = True

class CampaignOut(BaseModel):
    id: int
    name: str
    status: str
    agents: List[AgentOut] = []

    class Config:
        orm_mode = True

class CompanyOut(BaseModel):
    id: int
    name: str
    role: str
    campaigns: List[CampaignOut] = []

    class Config:
        orm_mode = True

class CampaignAgentOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class CompanyBase(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone: str
    role: Optional[str] = "user"

class CompanyCreate(CompanyBase):
    password: str  # plain password will be hashed

class CompanyUpdate(CompanyBase):
    pass

class CompanyOut(CompanyBase):
    id: int

    class Config:
        orm_mode = True