from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.utils.auth import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
ELEVENLABS_API_KEY  = 'sk_7f90efe9adbdaf466b305dc314fe4afccb8d2ccb00660e6a'

def get_current_company(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        company_id: str = payload.get("sub")
        if company_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    company = db.query(models.Company).filter(models.Company.id == int(company_id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
