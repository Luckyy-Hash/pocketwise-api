from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base properties for an Expense
class ExpenseBase(BaseModel):
    type: str # 'income' or 'expense'
    amount: float
    category: str
    description: Optional[str] = None
    payment_mode: str

# What we expect when React creates a new expense
class ExpenseCreate(ExpenseBase):
    user_id: int

# What the API returns back to React (includes the DB-generated ID and Date)
class Expense(ExpenseBase):
    id: int
    date: datetime
    user_id: int

    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy models

class Token(BaseModel):
    credential: str

# The raw SMS payload we expect to receive
class SMSPayload(BaseModel):
    raw_text: str
    user_id: int

class UserSettings(BaseModel):
    user_id: int
    min_balance: float

class BudgetBase(BaseModel):
    category: str
    limit_amount: float

class BudgetCreate(BudgetBase):
    user_id: int

class Budget(BudgetBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
