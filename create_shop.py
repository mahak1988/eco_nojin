import httpx, json, uuid

# Login as seller
r = httpx.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'seller@test.com', 'password': 'seller123'}, timeout=10)
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'X-CSRF-Token': 'test'}

marketplace_id = "9dec15dd-8f3f-457d-a1b9-9254b6696b55"

# Create shop with correct field names
r = httpx.post(f'http://127.0.0.1:8000/api/v1/marketplace/marketplaces/{marketplace_id}/shops', 
    json={
        'shop_name': 'Test Shop',
        'shop_description': 'A test shop'
    },
    headers=headers)
print('Create Shop:', r.status_code, r.text[:500])

# List shops
r = httpx.get(f'http://127.0.0.1:8000/api/v1/marketplace/marketplaces/{marketplace_id}/shops', headers=headers)
print('Shops:', r.status_code, r.text[:1000])