from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app import models
from app.utils.auth import decode_access_token, hash_password, verify_password, create_access_token
import random
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.username == form_data.username).first()
    if not company or not verify_password(form_data.password, company.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(company.id), "role": company.role})

    return {"access_token": access_token, "token_type": "bearer", "com_id": company.id, "role": company.role}

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(decode_access_token)
):
    company_id = token_data["sub"]  # sub is company ID
    company = db.query(models.Company).filter(models.Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not verify_password(request.old_password, company.password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    company.password = hash_password(request.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

# otp_store = {}  # temp in-memory store
# otp_verified_store = {} # track verified users

@router.post("/forgot-password")
def forgot_password(username: str, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.username == username).first()
    if not company:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(100000, 999999))

    otp_entry = models.OTPRequest(
        username=username,
        otp=otp,
        status="created"
    )
    db.add(otp_entry)
    db.commit()

    # TODO: send OTP via email/SMS
    print(f"OTP for {username}: {otp}")

    # return email as well
    return {
        "message": "OTP sent",
        "email": company.email
    }

class OTPRequestBody(BaseModel):
    otp: str

@router.post("/verify-otp")
def verify_otp(data: OTPRequestBody, db: Session = Depends(get_db)):
    otp = data.otp
    print("otp:", otp)

    otp_entry = db.query(models.OTPRequest).filter(
        models.OTPRequest.otp == otp,
        models.OTPRequest.status == "created",
        # models.OTPRequest.expires_at >= datetime.utcnow()
    ).first()

    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp_entry.status = "verified"
    db.commit()

    return {"message": "OTP verified"}

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    otp_entry = db.query(models.OTPRequest).filter(
        models.OTPRequest.username == request.username,
        models.OTPRequest.status == "verified"
    ).order_by(models.OTPRequest.created_at.desc()).first()

    if not otp_entry:
        raise HTTPException(status_code=400, detail="OTP not verified")

    company = db.query(models.Company).filter(models.Company.username == request.username).first()
    if not company:
        raise HTTPException(status_code=404, detail="User not found")

    company.password = hash_password(request.new_password)
    db.commit()

    # mark OTP as used
    otp_entry.status = "used"
    db.commit()

    return {"message": "Password reset successful"}

# @router.post("/reset-password")
# def reset_password(username: str, otp: str, new_password: str, db: Session = Depends(get_db)):
#     if otp_store.get(username) != otp:
#         raise HTTPException(status_code=400, detail="Invalid OTP")

#     company = db.query(models.Company).filter(models.Company.username == username).first()
#     if not company:
#         raise HTTPException(status_code=404, detail="User not found")

#     company.password = hash_password(new_password)
#     db.commit()
#     otp_store.pop(username, None)
#     return {"message": "Password reset successful"}