import httpx, json, uuid

# Login as seller
r = httpx.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'seller@test.com', 'password': 'seller123'}, timeout=10)
token = r.json()['access_token']
headers = {'Authorization': 'Bearer ' + token, 'X-CSRF-Token': 'test'}

shop_id = "26749ea3-93c7-4eea-8c9b-4c63caf9e625"

products = [
    {"shop_id": shop_id, "name": "Organic Apples", "sku": "ORG-APPLE-1KG", "price": "50000", "stock_qty": 50, "category": "fruit", "description": "Fresh organic apples", "village_id": "village-001"},
    {"shop_id": shop_id, "name": "Fresh Tomatoes", "sku": "FRESH-TOMATO-1KG", "price": "30000", "stock_qty": 30, "category": "vegetable", "description": "Fresh tomatoes", "village_id": "village-001"},
    {"shop_id": shop_id, "name": "Organic Honey", "sku": "ORG-HONEY-500G", "price": "200000", "stock_qty": 20, "category": "honey", "description": "Pure organic honey", "village_id": "village-001"},
]

for p in products:
    r = httpx.post('http://127.0.0.1:8000/api/v1/marketplace/products', json=p, headers=headers)
    name = p['name']
    print('Create Product', name, ':', r.status_code, '-', r.text[:300])

# List products
r = httpx.get('http://127.0.0.1:8000/api/v1/marketplace/products', params={'shop_id': shop_id}, headers=headers)
print('Products:', r.status_code, r.text[:1000])