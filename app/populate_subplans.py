import requests

# FastAPI endpoint
url = "http://127.0.0.1:8000/subplans/"

# Sample 10 subplans
sample_subplans = [
    {"pricing_id": 1, "title": "Basic Tier", "description": "Basic features", "price": 49.99},
    {"pricing_id": 1, "title": "Standard Tier", "description": "Standard features", "price": 99.99},
    {"pricing_id": 1, "title": "Premium Tier", "description": "Premium features", "price": 149.99},
    {"pricing_id": 2, "title": "Silver Plan", "description": "Silver plan for clients", "price": 59.99},
    {"pricing_id": 2, "title": "Gold Plan", "description": "Gold plan for clients", "price": 119.99},
    {"pricing_id": 2, "title": "Platinum Plan", "description": "Platinum plan for clients", "price": 179.99},
    {"pricing_id": 3, "title": "Starter Pack", "description": "Starter pack features", "price": 29.99},
    {"pricing_id": 3, "title": "Business Pack", "description": "Business pack features", "price": 79.99},
    {"pricing_id": 3, "title": "Enterprise Pack", "description": "Enterprise pack features", "price": 199.99},
    {"pricing_id": 3, "title": "Custom Plan", "description": "Custom pricing plan", "price": 249.99}
]

# POST each sample subplan
for subplan in sample_subplans:
    response = requests.post(url, json=subplan)
    if response.status_code in [200, 201]:
        print(f"✅ Created subplan: {subplan['title']}")
    else:
        print(f"❌ Failed to create {subplan['title']}: {response.status_code} {response.text}")

import json
import requests

with open("sample_subplans.json") as f:
    subplans = json.load(f)

url = "http://127.0.0.1:8000/subplans/"

for sp in subplans:
    res = requests.post(url, json=sp)
    if res.status_code in [200, 201]:
        print(f"✅ Created subplan: {sp['title']}")
    else:
        print(f"❌ Failed: {res.status_code} {res.text}")