import requests

url = "https://pocketwise-api.onrender.com/expenses/"
payload = {
    "type": "income",
    "amount": 100,
    "category": "Allowance",
    "description": "Test",
    "payment_mode": "Cash",
    "user_id": 1
}

res = requests.post(url, json=payload)
print(res.status_code)
print(res.text)
