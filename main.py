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
    # Now handles: "Rs.1,000.50", "Rs.100.99", "Rs. 500", etc.
    # Matches numbers with optional commas and 0-3 decimal places
    amount_match = re.search(r'(?i)(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.\d{1,3})?)', payload.raw_text)
    
    if not amount_match:
        raise HTTPException(status_code=400, detail="Could not detect a valid amount in the SMS")
    
    # Remove commas and convert to float
    amount_str = amount_match.group(1).replace(',', '')
    extracted_amount = float(amount_str)

    # 2. Determine if it's a debit (expense) or credit (income)
    text_lower = payload.raw_text.lower()
    if "credited" in text_lower or "received" in text_lower or "added" in text_lower:
        transaction_type = "income"
    else:
        transaction_type = "expense"

    # 3. Save the auto-parsed data to the database
    db_expense = models.Expense(
        type=transaction_type,
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

# --- BUDGETS ---
@app.post("/budgets/", response_model=schemas.Budget)
def update_budget(budget: schemas.BudgetCreate, db: Session = Depends(get_db)):
    # Check if budget for this category exists
    existing = db.query(models.Budget).filter(
        models.Budget.user_id == budget.user_id,
        models.Budget.category == budget.category
    ).first()

    if existing:
        existing.limit_amount = budget.limit_amount
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_budget = models.Budget(**budget.model_dump())
        db.add(db_budget)
        db.commit()
        db.refresh(db_budget)
        return db_budget

@app.get("/budgets/", response_model=list[schemas.Budget])
def read_budgets(user_id: int, db: Session = Depends(get_db)):
    budgets = db.query(models.Budget).filter(models.Budget.user_id == user_id).all()
    return budgets

# --- SETTINGS ---
@app.put("/users/settings", response_model=schemas.UserSettings)
def update_settings(settings: schemas.UserSettings, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == settings.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.min_balance = settings.min_balance
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "min_balance": user.min_balance}

@app.get("/users/{user_id}/settings", response_model=schemas.UserSettings)
def get_settings(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id, "min_balance": user.min_balance}
