import httpx, base64, json

users = ['test@demo.com', 'farmer@test.com', 'researcher@test.com', 'org@test.com', 'admin@test.com']
for email in users:
    r = httpx.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': email, 'password': 'admin123'}, timeout=10)
    if r.status_code == 200:
        token = r.json()['access_token']
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        print(f'{email}: role={decoded.get("role")}, user_id={decoded.get("user_id")}')