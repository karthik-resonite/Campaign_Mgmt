from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
from .database import Base

class CallLog(Base):
    __tablename__ = "call_logs"

    sid = Column(String, primary_key=True, index=True)
    from_number = Column(String, nullable=False)
    to_number = Column(String, nullable=False)
    status = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)  # hashed password
    email = Column(String, unique=True)
    phone = Column(String, unique=True)
    role = Column(String, default="user")
    agents = relationship("Agent", back_populates="company")
    campaigns = relationship("Campaign", back_populates="company")
    campaign_agents = relationship("CampaignAgent", back_populates="company")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    status = Column(String, default="Paused")  # <-- new column added

    # Relationships
    company = relationship("Company", back_populates="campaigns")
    customers = relationship("Customer", back_populates="campaign")
    campaign_agents = relationship("CampaignAgent", back_populates="campaign")

class CampaignAgent(Base):
    __tablename__ = "campaign_agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(Integer, ForeignKey("companies.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    gaming_offer = Column(String, nullable=True)
    company = relationship("Company", back_populates="campaign_agents")
    customers = relationship("Customer", back_populates="campaign_agent")
    campaign = relationship("Campaign", back_populates="campaign_agents")
    agent = relationship("Agent", back_populates="campaign_agents")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    campaign_agents_id = Column(Integer, ForeignKey("campaign_agents.id"))
    company = relationship("Company", back_populates="agents")
    campaign_agents = relationship("CampaignAgent", back_populates="agent")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String, index=True)
    email  = Column(String)
    status = Column(String, default="pending")  # pending, success, failed
    customer_interest = Column(String)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    campaign_agents_id = Column(Integer, ForeignKey("campaign_agents.id"))
    campaign = relationship("Campaign", back_populates="customers")
    campaign_agent = relationship("CampaignAgent", back_populates="customers")  # ✅ add
    source = Column(Text)

class OTPRequest(Base):
    __tablename__ = "otp_requests"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    otp = Column(String, nullable=False)
    status = Column(String, default="created")  # created, verified, used
    created_at = Column(DateTime, default=datetime.utcnow)
    # expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=5))

class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False)
    normalized_phone = Column(String, index=True)
    agent_id = Column(String(255), nullable=False)
    conversation_id = Column(String(255), nullable=False)
    language = Column(String(50), nullable=True)
    messages = Column(JSON, default=list)  # Stores transcript
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CRMLead(Base):
    __tablename__ = "crm_lead"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    status = Column(String(50), default="Pending")  # New, Contacted, Qualified, Converted
    created_at = Column(DateTime(timezone=True), server_default=func.now())