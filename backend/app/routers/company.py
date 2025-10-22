from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import schemas, crud, models
from app.database import get_db
from app.dependencies import get_current_company  # 👈 new import

router = APIRouter(prefix="/companies", tags=["Company"])

# Registration (public)
@router.post("/", response_model=schemas.Company)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    return crud.create_company(db, company)

# Protected route: Get one company
@router.get("/{company_id}", response_model=schemas.Company)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_company: models.Company = Depends(get_current_company)  # 🔒 JWT required
):
    db_company = crud.get_company(db, company_id)
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Optional: prevent access to others' data unless admin
    if current_company.role != "admin" and current_company.id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return db_company

# Protected route: Get all companies (admin only)
@router.get("/", response_model=List[schemas.Company])
def get_all_company(
    db: Session = Depends(get_db),
    current_company: models.Company = Depends(get_current_company)  # 🔒 JWT required
):
    if current_company.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return crud.get_all_company(db)
