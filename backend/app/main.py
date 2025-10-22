from fastapi import FastAPI,HTTPException,Depends
from app import models
from app.database import engine
from app.routers import company, auth, campaigns, calls
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, desc
import requests
import re
import os
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Company, Campaign, CampaignAgent, Agent, Customer, CallLog, Conversation, CRMLead  # your SQLAlchemy models
from app.schemas import CompanyOut, CampaignOut, AgentOut, CustomerOut, CampaignAgentOut, CompanyCreate, CompanyUpdate
from app.database import get_db
from twilio.rest import Client
from datetime import datetime
from sqlalchemy import extract
from fastapi import Query
from calendar import monthrange
from pydantic import BaseModel, EmailStr
from concurrent.futures import ThreadPoolExecutor
from operator import attrgetter
from collections import defaultdict
import unicodedata
from rapidfuzz import fuzz

# Create tables
models.Base.metadata.create_all(bind=engine)

ELEVENLABS_API_KEY = "sk_3c2a89de0706aa7b4b08fcad0764b3fa14448e143d396301"
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1/convai"
HEADERS = {"xi-api-key": ELEVENLABS_API_KEY}
AGENT_ID = "agent_2401k4d81z28ex6ta12eb84faesj"  # Replace with your actual agent ID

app = FastAPI(title="Campaign Management API")
app.include_router(auth.router)
app.include_router(company.router)
app.include_router(campaigns.router)
app.include_router(calls.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:5173", "https://c04002341658.ngrok-free.app","http://185.217.125.218:5173","https://redsocks.mu"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {"message": "Campaign API is running 🚀"}

account_sid = "##############################"
auth_token = "###############################"
client = Client(account_sid, auth_token)

def normalize_number(number: str) -> str:
    """Remove everything except digits (e.g., +, -, spaces)."""
    if not number:
        return ""
    return re.sub(r"\D", "", number)

@app.post("/sync-customer-status-with-call-logs")
def sync_customer_status_with_call_logs(db: Session = Depends(get_db)):
    # 1. Subquery to get latest call per unique to_number
    subquery = (
        db.query(
            CallLog.to_number,
            func.max(CallLog.start_time).label("latest_start")
        )
        .group_by(CallLog.to_number)
        .subquery()
    )

    # 2. Latest call log entries
    latest_logs = (
        db.query(CallLog)
        .join(
            subquery,
            (CallLog.to_number == subquery.c.to_number) &
            (CallLog.start_time == subquery.c.latest_start)
        )
        .all()
    )

    updated_customers = []

    print(f"?? Found {len(latest_logs)} latest call logs")

    # 3. Loop over each unique latest call log
    for log in latest_logs:
        normalized_to_number = normalize_number(log.to_number)
        print(f"\n?? Log SID: {log.sid}")
        print(f"  Original to_number: '{log.to_number}'")
        print(f"  Normalized to_number: '{normalized_to_number}'")

        # Try to match with customer
        customer = (
            db.query(Customer)
            .filter(
                func.replace(
                    func.replace(
                        func.replace(Customer.phone, '-', ''), ' ', ''
                    ), '+', ''
                ) == normalized_to_number
            )
            .first()
        )

        if customer:
            print(f"? MATCH FOUND ? Customer ID: {customer.id}, Phone: {customer.phone}")
            customer.status = log.status
            updated_customers.append({
                "customer_id": customer.id,
                "phone": customer.phone,
                "matched_with": log.to_number,
                "status": log.status
            })
        else:
            print(f"NO MATCH for {normalized_to_number} - checking why...")

            # DEBUG: get all similar numbers to inspect
            similar_customers = db.query(Customer).all()
            for c in similar_customers:
                normalized_customer = normalize_number(c.phone)
                if normalized_customer.endswith(normalized_to_number[-9:]):  # last digits
                    print(f"    Possible similar: ID={c.id}, phone={c.phone}, normalized={normalized_customer}")

    # 4. Commit updates
    db.commit()

    print(f"\n? Updated {len(updated_customers)} customers")

    return {
        "message": f"Updated {len(updated_customers)} customer(s) with latest call log status.",
        "updated_customers": updated_customers
    }

@app.post("/import-calls/")
def import_call_logs(db: Session = Depends(get_db)):
    # 1. Get the most recent start_time in the DB
    latest_call = db.query(CallLog).order_by(CallLog.start_time.desc()).first()
    start_time_after = latest_call.start_time if latest_call and latest_call.start_time else None

    # 2. Fetch calls from Twilio (after last start_time if available)
    calls = client.calls.list(
        from_="+18569344323",
        start_time=start_time_after,
        page_size=1000
    )

    imported_count = 0
    updated_count = 0

    for call in calls:
        existing_call = db.query(CallLog).filter(CallLog.sid == call.sid).first()

        if existing_call:
            # ? Update record if status or duration has changed
            updated = False

            new_status = call.status
            new_duration = int(call.duration) if call.duration else None

            if existing_call.status != new_status:
                existing_call.status = new_status
                updated = True

            if existing_call.duration != new_duration:
                existing_call.duration = new_duration
                updated = True

            if updated:
                existing_call.start_time = call.start_time  # ensure consistency
                updated_count += 1
        else:
            # ? Insert new record
            db_call = CallLog(
                sid=call.sid,
                from_number=call.from_formatted or call.from_,
                to_number=call.to_formatted or call.to,
                status=call.status,
                start_time=call.start_time if call.start_time else None,
                duration=int(call.duration) if call.duration else None
            )
            db.add(db_call)
            imported_count += 1

    db.commit()
    return {
        "message": f"{imported_count} new calls imported, {updated_count} updated."
    }

def list_conversations(agent_id=AGENT_ID, limit=100):
    params = {"limit": limit, "agent_id": agent_id}
    response = requests.get(f"{ELEVENLABS_BASE}/conversations", headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

# -----------------------------
# Route: /agent-metrics/
# -----------------------------

@app.get("/agent-metrics/")
def agent_metrics(
    db: Session = Depends(get_db),
    month_year: str = Query(..., regex=r'^\d{4}-\d{2}$')  # Format: YYYY-MM
):
    """
    Calculate agent metrics for a given month-year using CallLog table.
    """
    try:
        year, month = map(int, month_year.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month_year format. Use YYYY-MM.")

    # Get start and end of the month
    start_date = datetime(year, month, 1)
    end_day = monthrange(year, month)[1]
    end_date = datetime(year, month, end_day, 23, 59, 59)

    # Query filtered call logs
    calls = db.query(CallLog).filter(CallLog.start_time >= start_date, CallLog.start_time <= end_date).all()

    if not calls:
        return JSONResponse(content={
            "total_calls": 0,
            "avg_duration": "0m 0s",
            "success_rate": 0.0,
            "conversion_rate": 0.0
        })

    total_calls = len(calls)
    successful_calls = [call for call in calls if call.status == 'completed']
    durations = [call.duration or 0 for call in calls]

    success_count = len(successful_calls)
    avg_duration_secs = sum(durations) / total_calls if total_calls else 0
    success_rate = (success_count / total_calls) * 100 if total_calls else 0

    minutes, seconds = divmod(int(avg_duration_secs), 60)
    avg_duration_formatted = f"{minutes}m {seconds}s"

    return JSONResponse(content={
        "total_calls": total_calls,
        "avg_duration": avg_duration_formatted,
        "success_rate": round(success_rate, 2),
        "conversion_rate": round(success_rate, 2)
    })

@app.get("/calls-per-week/")
def calls_per_week(db: Session = Depends(get_db)):
    today = datetime.utcnow()
    current_year = today.year
    current_month = today.month

    # Fetch calls from current month
    calls = db.query(CallLog).filter(
        extract('year', CallLog.start_time) == current_year,
        extract('month', CallLog.start_time) == current_month
    ).all()

    # Initialize buckets for 4 weeks
    week_counts = [0, 0, 0, 0]

    for call in calls:
        if not call.start_time:
            continue

        day = call.start_time.day

        if 1 <= day <= 7:
            week_counts[0] += 1
        elif 8 <= day <= 14:
            week_counts[1] += 1
        elif 15 <= day <= 21:
            week_counts[2] += 1
        else:
            week_counts[3] += 1

    data = {
        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "datasets": [
            {
                "label": "Calls",
                "data": week_counts,
                "fill": True,
                "borderColor": "#14648C",
                "backgroundColor": "rgba(20,100,140,0.2)",
                "tension": 0.4
            }
        ]
    }

    return JSONResponse(content=data)

@app.get("/companies/", response_model=List[CompanyOut])
def list_companies(db: Session = Depends(get_db)):
    print('hi')
    companies = db.query(Company).filter(Company.role == 'user').all()
    return companies

@app.get("/companies/{company_id}/campaigns/", response_model=List[CampaignOut])
def get_campaigns_for_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Eager load campaigns and their agents & customers (you might need joins or subqueryload)
    return company.campaigns

@app.get("/campaigns/{campaign_id}/agents/", response_model=List[CampaignAgentOut])
def get_campaign_agents_for_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign_agents = campaign.campaign_agents
    print("Returning campaign agents:", [vars(ca) for ca in campaign_agents])

    return campaign_agents
@app.get("/agents/{agent_id}/customers/", response_model=List[dict])
def get_customers_for_agent(agent_id: int, db: Session = Depends(get_db)):
    # Get customers for this agent
    customers = db.query(Customer).filter(Customer.campaign_agents_id == agent_id).all()

    result = []
    for customer in customers:
        # Fetch conversation(s) where customer.phone matches conversation.phone_number
        conversations = (
            db.query(Conversation)
            .filter(Conversation.phone_number == customer.phone)
            .all()
        )

        # Convert conversations into dicts
        conv_list = []
        for conv in conversations:
            conv_list.append({
                "id": conv.id,
                "phone_number": conv.phone_number,
                "agent_id": conv.agent_id,
                "conversation_id": conv.conversation_id,
                "language": conv.language,
                "messages": conv.messages,
                "created_at": conv.created_at
            })

        # Append customer + conversation dict
        result.append({
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "status": customer.status,
            "conversation": customer.conversation,  # if you store raw text
            "campaign_id": customer.campaign_id,
            "campaign_agents_id": customer.campaign_agents_id,
            "conversations": conv_list   # <-- appended conversations list
        })

    return result
@app.delete("/campaigns/{campaign_id}")
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db.delete(campaign)
    db.commit()
    return {"detail": "Campaign deleted"}

@app.post("/companies/", response_model=CompanyOut)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.username == company.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_company = Company(
        name=company.name,
        username=company.username,
        email=company.email,
        phone=company.phone,
        password=company.password,  # Ideally hash this!
        role=company.role
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company

# Update user
@app.post("/companies/{company_id}", response_model=CompanyOut)
def update_company(company_id: int, update_data: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    for key, value in update_data.dict().items():
        setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return company

class LeadCreate(BaseModel):
    name: Optional[str]
    number: str
    email: Optional[EmailStr]

@app.post("/api/add_data/")
async def add_data(lead: LeadCreate, db: Session = Depends(get_db)):
    phone = lead.number

    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")

    # Check if phone already exists
    existing = db.query(Customer).filter(Customer.phone == phone).first()
    if existing:
        raise HTTPException(status_code=409, detail="Lead with this phone number already exists")

    new_lead = Customer(
        name=lead.name,
        phone=phone,
	status='Pending',
	campaign_id=campaign_id,
        source='form'
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    return {"message": "Lead saved successfully"}

# -------------------- KEYWORDS --------------------
INTERESTED_KEYWORDS_WEIGHTED = {
    # Buying Intent
    "i'm interested": 5,
    "looking to buy": 4,
    "want to buy": 4,
    "interested in buying": 5,
    "send me the details": 3,
    "can you share the brochure": 3,
    "brochure": 1,
    "floor plan": 1,
    "price per": 3,
    "what's the price": 4,
    "how much is it": 4,
    "price range": 3,
    "payment plan": 3,
    "interested in off-plan": 4,
    "investment opportunity": 4,
    "ready to move": 5,
    "title deed": 3,
    "market value": 3,
    "mortgage": 3,
    "commission": 2,
    "down payment": 3,
    "handover date": 3,
    "payment terms": 3,
    "when can I view": 4,
    "book a viewing": 4,
    "site visit": 4,
    "visit the site": 4,
    "book a call": 3,
    "what's the next step": 4,
    "agent follow-up": 3,
    "i want to invest": 5,
    "property investment": 4,
    "ROI": 4,
    "expected returns": 4,
    "how soon can we close": 5,
    "let's proceed": 5,
    "send me more info": 3,
    "shortlist this property": 4,
    "reserve the unit": 4,
    "i like this property": 4,
    "i love this location": 4,
    "this looks perfect": 4,
    "ready to proceed": 5,
    "let's finalize": 5,
    "i'm serious": 5,
    "i'm ready": 5,
    "i've got my budget": 4,
    "looking for options": 3,
    "comparing a few options": 3,
    "can we negotiate": 3,
    "is it available": 3,
    "let's move forward": 4,
    # Selling Intent
    "planning to sell": 4,
    "want to sell": 4,
    "looking to list": 4,
    "want to list my property": 4,
    "how fast can you sell": 3,
    "how much can I get": 4,
    "market appraisal": 3,
    "valuation": 3,
    "i want to rent it": 4,
    "i need tenants": 4,
    "how do you market it": 3,
    "exclusive listing": 3,
    "get leads": 3,
    "list with you": 3,
    "commission structure": 2,
}

NOT_INTERESTED_KEYWORDS_WEIGHTED = {
    "not interested": 5,
    "not looking to buy": 5,
    "not looking to sell": 5,
    "already purchased": 5,
    "already sold": 5,
    "already rented": 5,
    "just checking prices": 2,
    "only checking prices": 2,
    "not interested": 5,
    "not planning right now": 4,
    "call me later": 2,
    "i'm busy": 3,
    "send me a whatsapp": 2,
    "no time": 3,
    "satisfied with my current property": 4,
    "don't have budget": 4,
    "not in dubai": 4,
    "out of the country": 4,
    "just exploring": 2,
    "don't want to list": 4,
    "i'm not selling": 5,
    "don't want to rent": 4,
    "not ready": 3,
    "maybe next year": 3,
    "no plans to buy": 4,
    "not in the market": 4,
    "i'm not investing": 5,
    "not now": 3,
    "not at the moment": 3,
    "leave me alone": 5,
    "remove me from your list": 5,
    "don't call again": 5,
    "already working with another agent": 5,
    "already listed elsewhere": 5,
    "i have an agent": 5,
    "no thanks": 5,
    "stop calling": 5,
}

MAYBE_INTEREST_KEYWORDS_WEIGHTED = {
    "i'll think about it": 3,
    "i'll let you know": 3,
    "maybe in a few months": 3,
    "call me next week": 2,
    "call me later": 2,
    "once i get my funds": 3,
    "i need time": 3,
    "i'll discuss it": 3,
    "not sure yet": 3,
    "i'll get back to you": 3,
    "i'm still deciding": 3,
    "let me talk to my spouse": 3,
    "let me talk to my partner": 3,
    "checking options": 3,
    "considering a few things": 3,
    "we'll see": 2,
    "i might": 2,
    "maybe later": 2,
    "possibly": 2,
    "i like it but not now": 3,
    "need to arrange financing": 3,
    "waiting for my budget": 3,
    "waiting for approval": 3,
    "once I finalize my decision": 3,
    "when I'm ready": 3,
    "when I return to Dubai": 3,
    "maybe after a month": 2,
    "i'll check my schedule": 2,
    "thinking about selling": 3,
    "thinking about buying": 3,
    "i'll save your number": 2,
}

	
# -------------------- HELPERS --------------------
def normalize_phonenumber(number: str) -> str:
    """Remove all non-digit characters but keep country code if present."""
    if not number:
        return ""
    return re.sub(r"\D", "", number)

def clean_text(text: str) -> str:
    """Normalize text: lowercase, remove punctuation, fix common contractions, remove accents."""
    if not text:
        return ""
    # Normalize unicode (remove accents, etc.)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    # Remove punctuation except apostrophes (helps with "don't", "i'm")
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    # Fix common contractions
    text = text.replace("dont", "don't")
    text = text.replace("im", "i'm")
    text = text.replace("whats", "what's")
    # Collapse extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

# -------------------- MATCHING --------------------
def keyword_match(text: str, keywords: list[str]) -> int:
    """Return the number of keyword matches in the text (regex boundary match)."""
    count = 0
    for kw in sorted(keywords, key=len, reverse=True):
        # \b ensures whole word/phrase match
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text):
            count += 1
    return count

def weighted_fuzzy_keyword_match(text: str, keywords_weighted: dict[str, int], threshold: int = 70) -> int:
    """Return the weighted sum of matched keywords in the text using fuzzy matching."""
    total_score = 0
    for kw, weight in keywords_weighted.items():
        # Check exact substring match first for efficiency
        if kw in text:
            total_score += weight
            continue
        # Otherwise, fuzzy match
        score = fuzz.partial_ratio(kw, text)
        if score >= threshold:
            total_score += weight
    return total_score

def find_first_occurrence(text: str, keywords: list[str], threshold: int = 80) -> int:
    """
    Return the earliest index where any keyword approximately appears in the text,
    using fuzzy partial matching.
    """
    best_pos = float('inf')
    for kw in keywords:
        score = fuzz.partial_ratio(kw, text)
        if score >= threshold:
            # Find approximate position by searching the lowercased kw in text
            pos = text.find(kw)
            if pos == -1:
                # fallback: try to match first few words of kw
                first_word = kw.split()[0]
                pos = text.find(first_word)
            if pos != -1 and pos < best_pos:
                best_pos = pos
    return best_pos

# -------------------- CLASSIFICATION --------------------
def classify_interest(messages: list[dict]) -> str:
    """
    Classify customer interest level based on USER messages only.
    Priority: Not Interested > Interested > Maybe (with tie-breaker by first occurrence).
    """
    # Combine all user messages
    raw_text = " ".join(
        msg.get("message", "") for msg in messages
        if isinstance(msg, dict) and msg.get("role") == "user"
    )
    text = clean_text(raw_text)
    # Scores
    not_interested_score = weighted_fuzzy_keyword_match(text, NOT_INTERESTED_KEYWORDS_WEIGHTED)
    interested_score = weighted_fuzzy_keyword_match(text, INTERESTED_KEYWORDS_WEIGHTED)
    maybe_score = weighted_fuzzy_keyword_match(text, MAYBE_INTEREST_KEYWORDS_WEIGHTED)

    scores = {
        "Not Interested": not_interested_score,
        "Interested": interested_score,
        "Maybe": maybe_score
    }

    print(f"[DEBUG] Cleaned text: {text}")
    print(f"[DEBUG] Scores: {scores}")

    # If no matches
    if max(scores.values()) == 0:
        return ""

    # Tie-breaker positions
    first_not_interested = find_first_occurrence(text, list(NOT_INTERESTED_KEYWORDS_WEIGHTED.keys()))
    first_interested = find_first_occurrence(text, list(INTERESTED_KEYWORDS_WEIGHTED.keys()))

    # Priority handling:
    if not_interested_score > interested_score and not_interested_score >= maybe_score:
        return "Not Interested"
    elif not_interested_score == interested_score and not_interested_score > 0:
        # Tie: Whichever appears first in the text wins
        if first_interested < first_not_interested:
            return "Interested"
        else:
            return "Not Interested"
    elif interested_score >= maybe_score:
        return "Interested"
    else:
        return "Follow Up"

def format_duration(seconds: int) -> str:
    if seconds is None:
        return "0s"
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    if s > 0 or not parts:
        parts.append(f"{s}s")
    return " ".join(parts)

# -------------------- API --------------------
@app.get("/api/get_data/{campaign_id}")
def get_data(campaign_id: int, db: Session = Depends(get_db)):
    # 1. Load all leads/customers for the given campaign
    leads = db.query(models.Customer).filter(models.Customer.campaign_id == campaign_id).all()

    # 2. Build normalized map: lead_id -> normalized phone
    normalized_numbers = {
        lead.id: normalize_phonenumber(lead.phone or "")
        for lead in leads
    }
    print("Normalized lead phone numbers:", normalized_numbers)

    # 3. Fetch conversations matching normalized phone
    all_convos = db.query(models.Conversation).filter(
        models.Conversation.normalized_phone.in_(normalized_numbers.values())
    ).all()

    print("Normalized conversation phone numbers:")
    for convo in all_convos:
        print(f"Convo ID: {convo.id}, Normalized Phone: {convo.normalized_phone}")

    convo_map = defaultdict(list)
    for convo in all_convos:
        convo_map[convo.normalized_phone].append(convo)

    # 4. Fetch call logs and map normalized number -> list of logs
    all_calllogs = db.query(models.CallLog).all()
    calllog_map = defaultdict(list)
    for cl in all_calllogs:
        norm_to = normalize_phonenumber(cl.to_number or "")
        calllog_map[norm_to].append(cl)

    # 5. Classification per lead (based on LATEST conversation)
    def classify_for_lead(lead):
        norm = normalized_numbers.get(lead.id, "")
        convos = convo_map.get(norm, [])
        logs = calllog_map.get(norm, [])

        # Find latest conversation
        latest_convo = None
        if convos:
            latest_convo = max(convos, key=attrgetter('created_at'))

        messages_to_classify = latest_convo.messages if latest_convo and latest_convo.messages else []
        customer_interest = classify_interest(messages_to_classify)

        return (lead.id, customer_interest, convos, logs)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(classify_for_lead, leads))

    # 6. Build response
    response = []
    for lead_id, customer_interest, convos, logs in results:
        lead = next((l for l in leads if l.id == lead_id), None)
        if not lead:
            continue

        lead.customer_interest = customer_interest
        sorted_logs = sorted(
            logs,
            key=lambda cl: cl.start_time or datetime.min,
            reverse=True
        )
        # Call logs
        calllogs_data = []
        for cl in sorted_logs:
            formatted_start_time = cl.start_time.strftime("%Y-%m-%d %H:%M:%S") if cl.start_time else None
            calllogs_data.append({
                "sid": cl.sid,
                "from_number": cl.from_number,
                "to_number": cl.to_number,
                "status": cl.status,
                "start_time": formatted_start_time,
                "duration": format_duration(cl.duration)
            })

        # Conversations
        conversation_data = []
        for convo in convos:
            conversation_data.append({
                "id": convo.id,
                "conversation_id": convo.conversation_id,
                "agent_id": convo.agent_id,
                "phone_number": convo.phone_number,
                "language": convo.language or "",
                "messages": convo.messages,
                "created_at": convo.created_at.isoformat() if convo.created_at else None
            })

        response.append({
            "id": lead.id,
            "name": lead.name,
            "phone": lead.phone,
            "status": lead.status,
            "customer_interest": customer_interest,
            "conversations": conversation_data,
            "call_logs": calllogs_data
        })

    db.commit()
    return JSONResponse(content=response)

@app.get("/leads/{pk}/")
def delete_lead(pk: int, db: Session = Depends(get_db)):
    lead = db.query(Customer).filter(Customer.id == pk).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db.delete(lead)
    db.commit()

    return {"message": "Lead deleted successfully"}
