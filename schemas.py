from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Base properties for an Expense
class ExpenseBase(BaseModel):
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
