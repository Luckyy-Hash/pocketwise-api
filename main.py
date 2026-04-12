from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal
import re
from google.oauth2 import id_token
from google.auth.transport import requests

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to your Vercel URL later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROUTES ---

@app.post("/auth/login")
def login(token: schemas.Token, db: Session = Depends(get_db)):
    try:
        # Verify the token is meant specifically for PocketWise
        idinfo = id_token.verify_oauth2_token(
            token.credential, 
            requests.Request(), 
            "541008734402-4ttreb672mj2utp4bbqsqljd70o3bp16.apps.googleusercontent.com"
        )
        email = idinfo['email']
        name = idinfo.get('name', '')

        # Check if user exists
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            # Create user
            user = models.User(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)

        return {"user_id": user.id, "email": user.email, "name": user.name}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")


@app.post("/expenses/", response_model=schemas.Expense)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    # Convert the Pydantic schema to a SQLAlchemy model
    db_expense = models.Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/expenses/", response_model=list[schemas.Expense])
def read_expenses(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # THE PRIVACY FILTER: .filter(models.Expense.user_id == user_id)
    expenses = db.query(models.Expense).filter(models.Expense.user_id == user_id).offset(skip).limit(limit).all()
    return expenses

@app.post("/expenses/sms/", response_model=schemas.Expense)
def parse_and_save_sms(payload: schemas.SMSPayload, db: Session = Depends(get_db)):
    # 1. The Regex Hunt for the Amount
    # Looks for "Rs.", "INR", or "₹" followed by numbers and optional decimals
    amount_match = re.search(r'(?i)(?:rs\.?|inr|₹)\s*(\d+(?:\.\d{1,2})?)', payload.raw_text)
    
    if not amount_match:
        raise HTTPException(status_code=400, detail="Could not detect a valid amount in the SMS")
    
    extracted_amount = float(amount_match.group(1))

    # 2. Determine if it's a debit (expense) or credit (income)
    # For now, we will focus on routing debits to expenses
    if "credited" in payload.raw_text.lower():
        raise HTTPException(status_code=400, detail="This looks like income, not an expense.")

    # 3. Save the auto-parsed data to the database
    db_expense = models.Expense(
        amount=extracted_amount,
        category="Other", # Default category for SMS
        description=f"Auto-parsed SMS",
        payment_mode="UPI/GPay",
        user_id=payload.user_id
    )
    
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    return db_expense
