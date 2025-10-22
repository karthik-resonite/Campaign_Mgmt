from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app import schemas, crud, models
from app.database import get_db
from app.dependencies import get_current_company
#from app.routers.calls import make_call as make_call_internal

router = APIRouter(prefix="/campaigns", tags=["Campaign"])

@router.post("/new_campaigns")
def create_new_campaign(campaign: schemas.CampaignCreate1, db: Session = Depends(get_db), current_user=Depends(get_current_company)):
    # assuming current_user has company_id
    company_id = current_user.id
    if not company_id:
        raise HTTPException(status_code=400, detail="Company not found for the user")
    
    db_campaign = crud.create_campaign1(db, campaign, company_id)
    return db_campaign

@router.post("/", response_model=schemas.Campaign)
async def create_campaign_endpoint(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    # email: str = Form(...),
    campaign_id: int = Form(...),
    company_id: int = Form(...),
    agents: str = Form(...),
    csv_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_company: models.Company = Depends(get_current_company)
):
    print("📥 Received form data:")
    print(" - name:", name)
    print(" - campaign_id:", campaign_id)
    print(" - company_id:", company_id)
    print(" - agents:", agents)
    print(" - file name:", csv_file.filename)

    if current_company.id != company_id and current_company.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    file_bytes = await csv_file.read()

    campaign_in = schemas.CampaignCreate(
        name=name,
        campaign_id=campaign_id,
        company_id=company_id,
        agents=[a.strip() for a in agents.split(",")],
    )
    print("📦 Parsed CampaignCreate:", campaign_in.dict())

    print("👉 Calling crud.create_campaign")
    db_campaign =  crud.create_campaign(db, campaign_in, file_bytes, csv_file.filename)
    # Prepare payload for make_call
    #payload = schemas.CallPayload(type="agent", id=db_campaign.id)

    # Run asynchronously in the background so it doesn't block response
    #background_tasks.add_task(make_call_internal, payload, db)

    return db_campaign

@router.get("/get")
def get_campaigns(
    db: Session = Depends(get_db),
    current_company: models.Company = Depends(get_current_company)
):
    print('hi')
    # If not admin, only show campaigns from the current company
    if current_company.role != "admin":
        campaigns = db.query(models.Campaign).filter(
            models.Campaign.company_id == current_company.id
        ).all()
    else:
        campaigns = db.query(models.Campaign).all()

    return [{"id": c.id, "name": c.name} for c in campaigns]

@router.get("/get_campaign", response_model=list[schemas.CampaignCreate2])
def get_campaigns(
    db: Session = Depends(get_db),
    current_company: models.Company = Depends(get_current_company)
):
    print('hii')
    # Base query depending on role
    base_query = db.query(models.Campaign)
    if current_company.role != "admin":
        base_query = base_query.filter(models.Campaign.company_id == current_company.id)

    campaigns = base_query.all()
    response = []

    for campaign in campaigns:
        # Count total customers
        total_customers = db.query(func.count(models.Customer.id)).filter(
            models.Customer.campaign_id == campaign.id
        ).scalar()

        # Count by customer interest
        interested_count = db.query(func.count(models.Customer.id)).filter(
            models.Customer.campaign_id == campaign.id,
            func.lower(models.Customer.customer_interest) == 'interested'
        ).scalar()

        not_interested_count = db.query(func.count(models.Customer.id)).filter(
            models.Customer.campaign_id == campaign.id,
            func.lower(models.Customer.customer_interest) == 'not interested'
        ).scalar()

        maybe_count = db.query(func.count(models.Customer.id)).filter(
            models.Customer.campaign_id == campaign.id,
            func.lower(models.Customer.customer_interest) == 'maybe'
        ).scalar()

        # Add to response with extra fields
        response.append({
            "id": campaign.id,
            "name": campaign.name,
            "email": campaign.email,
            "created_at": campaign.created_at,
            "status": campaign.status,
            "company_id": campaign.company_id,
            "total_customers": total_customers,
            "interested_customers": interested_count,
            "not_interested_customers": not_interested_count,
            "maybe_customers": maybe_count
        })

    return response

@router.get("/{campaign_id}/customers")
def get_customers_by_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_company: models.Company = Depends(get_current_company)
):
    # Only fetch customers of this company (unless admin)
    query = db.query(models.Customer).filter(
        models.Customer.campaign_id == campaign_id
    )

    if current_company.role != "admin":
        query = query.filter(models.Campaign.company_id == current_company.id)

    customers = query.all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "status": c.status,
            "conversation": c.conversation
        }
        for c in customers
    ]