import httpx, json

# Login as admin
r = httpx.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'admin@test.com', 'password': 'admin123'}, timeout=10)
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'X-CSRF-Token': 'test'}

marketplace_id = "9dec15dd-8f3f-457d-a1b9-9254b6696b55"

# Approve marketplace (approve is query param)
r = httpx.post(f'http://127.0.0.1:8000/api/v1/marketplace/marketplaces/{marketplace_id}/approve?approve=true', 
    headers=headers)
print('Approve Marketplace:', r.status_code, r.text[:500])

# List marketplaces
r = httpx.get('http://127.0.0.1:8000/api/v1/marketplace/marketplaces', headers=headers)
print('Marketplaces:', r.status_code, r.text[:1000])