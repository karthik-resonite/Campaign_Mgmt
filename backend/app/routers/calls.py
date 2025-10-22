import re
from fastapi import BackgroundTasks, APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app import models, database, schemas, dependencies
from elevenlabs import ElevenLabs  # import ElevenLabs SDK
import httpx
import traceback

router = APIRouter()


# === ElevenLabs Call Function ===
def make_call_with_11labs(to_number: str, name: str, agent: str):
    try:
        client = ElevenLabs(api_key=dependencies.ELEVENLABS_API_KEY)
        agent_id = agent if agent else "agent_2401k4d81z28ex6ta12eb84faesj"
        phone_id = "phnum_2101k74am5d1eac88ccrspm9p8q9"
        print(f":telephone_receiver: Making call to {to_number}")
        conversation_data = {
            "type": "conversation_initiation_client_data",
            "dynamic_variables": {
                "customer_name": name
            }
        }
        client.conversational_ai.twilio.outbound_call(
            agent_id=agent_id,
            agent_phone_number_id=phone_id,
            to_number=to_number,
            conversation_initiation_client_data=conversation_data
        )
        return {"message": "Call initiated successfully", "status": "success"}
    except Exception as e:
        print(f":x: Error making call to {to_number}: {e}")
        return {"error": str(e), "status": "failed"}

def normalize_phone(phone):
    return re.sub(r'\D', '', phone)

# === End Call ===


async def call_api(api_url: str):
    print(f"Calling API: {api_url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url)
            print(f"API Response Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"API {api_url} failed with status {response.status_code}")
    except httpx.HTTPStatusError as e:
        print(f"Error during API call to {api_url}: {e}")
    except Exception as e:
        print(f"Unexpected error during API call to {api_url}: {e}")

async def call_apis_in_sequence(api_url_1: str, api_url_2: str):
    # Call first API
    await call_api(api_url_1)
    # After the first call finishes, call the second
    await call_api(api_url_2)

@router.post("/end_call")
async def end_call(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    api_url_1 = "https://redsocks.mu:9000/import-calls/"
    api_url_2 = "https://redsocks.mu:9000/sync-customer-status-with-call-logs"
    
    background_tasks.add_task(call_apis_in_sequence, api_url_1, api_url_2)
    print("Status: Call ended, APIs triggered in the background.")
    
    try:
        data = await request.json()
        print(f"Full data received: {data}")

        if data.get("type") == "call_initiation_failure":
            print('Failed to call')
            return {"status": "ok", "message": "Call initiation failure"}

        transcript = data.get("data", {}).get("transcript", [])
        phone_number = (
            data.get("data", {}).get("metadata", {}).get("phone_call", {}).get("external_number")
            or data.get("data", {}).get("conversation_initiation_client_data", {}).get("dynamic_variables", {}).get("system__caller_id")
            or "Unknown"
        )
        print(f"Extracted phone number: {phone_number}")

        # Extracting messages
        messages = []
        for entry in transcript:
            if "role" in entry and "message" in entry:
                message = entry["message"].strip() if entry["message"] else None
                if entry["role"] in ["agent", "user"] and message:
                    messages.append({"role": entry["role"], "message": message})
            else:
                print(f"Skipping entry with missing 'role' or 'message': {entry}")
        
        print(f"Processed messages: {messages}")

        agent_map = {
            "agent_01jxz81z4jew7b5j5memx0xcxc": ("Inbound", "English"),
            "agent_01jy1w83waeeks5ycz7wk2bsrm": ("Outbound", "English"),
            "agent_01jy1wy726f1d89zzjc3pq342z": ("Inbound", "Hindi"),
            "agent_01jy1y877yfa1vd9w8z7pkp405": ("Outbound", "Hindi"),
        }

        agent_id = data.get("data", {}).get("agent_id")
        conversation_id = data.get("data", {}).get("conversation_id")

        print(f"Agent ID: {agent_id}, Conversation ID: {conversation_id}")

        # Extract name, email, dob
        name, email, dob = None, None, None
        for msg in messages:
            if msg["role"] == "user":
                text = msg["message"].lower()
                if not name and "my name is" in text:
                    name = text.split("my name is")[-1].strip().split(" ")[0]
                if not email:
                    email_match = re.search(
                        r"[\w\.-]+@[\w\.-]+(?:\.[a-z]{2,})?",  # Relaxed email match
                        text.replace(" at ", "@").replace(" dot ", ".")
                    )
                    if email_match:
                        email = email_match.group(0)
                if not dob:
                    dob_match = re.search(r"\b(?:\d{1,2})[-/](?:\d{1,2})[-/](?:\d{2,4})\b", text)
                    if dob_match:
                        dob = dob_match.group(0)

        print("Extracted name:", name)
        print("Extracted email:", email)
        print("Extracted dob:", dob)

        mode, language = agent_map.get(agent_id, ("unknown", None))

        conversation = models.Conversation(
            phone_number=phone_number,
            agent_id=agent_id,
            conversation_id=conversation_id,
            language=language,
            messages=messages,
            normalized_phone=normalize_phone(phone_number)
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        print(f"Inserted conversation with ID: {conversation.id}")
        return {"status": "ok"}
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Stack Trace:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# === Call (Webhook Endpoint) ===
@router.post("/call")
async def call(request: Request):
    try:
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
        else:
            form = await request.form()
            data = dict(form)

        call_sid = data.get("CallSid")
        from_number = data.get("From")
        to_number = data.get("To")
        call_status = data.get("CallStatus")

        print(f"New conversation started: CallSid={call_sid}, From={from_number}, To={to_number}, Status={call_status}")
        return {"message": "Conversation data received", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")

# === Make Call (Trigger outbound calls for CRM leads) ===
@router.post("/make_call")
async def make_call(payload: schemas.CallPayload, db: Session = Depends(database.get_db)):
    print("payload", payload)

    if payload.type == "campaign":
        leads = db.query(models.Customer).filter(
            # models.Customer.status != "completed",
            models.Customer.campaign_id == payload.id
        ).all()

        campaign = db.query(models.Campaign).filter(models.Campaign.id == payload.id).first()
        org_name = campaign.company.name if campaign and campaign.company else "Unknown"

        agent = db.query(models.Agent).filter(models.Agent.campaign_id == payload.id).first()
        agent_id = agent.name if agent else "Unknown"

    elif payload.type == "agent":
        leads = db.query(models.Customer).filter(
            models.Customer.status != "completed",
            models.Customer.campaign_agents_id == payload.id
        ).all()

        campaign_agent = db.query(models.CampaignAgent).filter(models.CampaignAgent.id == payload.id).first()
        org_name = campaign_agent.company.name if campaign_agent and campaign_agent.company else "Unknown"

        agent = db.query(models.Agent).filter(models.Agent.campaign_agents_id == payload.id).first()
        agent_id = agent.name if agent else "Unknown"

    else:
        leads = []
        org_name = "Unknown"
        agent_id = "Unknown"

    print('leads:', leads)
    print('org name:', org_name)
    print('agent name:', agent_id)

    for item in leads:
        phone = item.phone
        name = item.name
        result = make_call_with_11labs(phone, name, agent_id)  # optionally pass agent_id too if needed
        print(f"Call result for {phone}: {result}")

        # Optionally update lead status
        if result.get("status") == "success":
            item.status = "Contacted"
            db.add(item)
            db.commit()

    return {"message": "Call process completed"}
