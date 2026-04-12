from database import engine
from sqlalchemy import text

try:
    with engine.connect() as con:
        con.execute(text("ALTER TABLE users ADD COLUMN min_balance FLOAT DEFAULT 1000"))
        con.commit()
    print("Column 'min_balance' added successfully!")
except Exception as e:
    print("Error:", e)
