import httpx, json, uuid, time

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

def get_headers(token):
    return {'Authorization': f'Bearer {token}', 'X-CSRF-Token': 'test', 'Idempotency-Key': str(uuid.uuid4())}

def get_auth_headers(token):
    return {'Authorization': f'Bearer {token}', 'X-CSRF-Token': 'test'}

# Login seller
r = httpx.post(f'{API_V1}/auth/login', json={'email': 'seller@test.com', 'password': 'seller123'}, timeout=30)
seller_token = r.json()['access_token']
print('Seller logged in')

# Login buyer
r = httpx.post(f'{API_V1}/auth/login', json={'email': 'buyer@test.com', 'password': 'buyer123'}, timeout=30)
buyer_token = r.json()['access_token']
print('Buyer logged in')

# Fund buyer wallet
headers = get_headers(buyer_token)
r = httpx.post(f'{API_V1}/finance/wallet/earn', json={'category': 'education', 'quantity': '10'}, headers=headers, timeout=30)
print('Fund Wallet:', r.status_code, r.json())

# Check buyer wallet
r = httpx.get(f'{API_V1}/finance/wallet', headers=get_auth_headers(buyer_token), timeout=30)
print('Buyer Wallet:', r.status_code, r.json())

# Check seller wallet
r = httpx.get(f'{API_V1}/finance/wallet', headers=get_auth_headers(seller_token), timeout=30)
print('Seller Wallet (before):', r.status_code, r.json())

# List products
marketplace_id = '9dec15dd-8f3f-457d-a1b9-9254b6696b55'
r = httpx.get(f'{API_V1}/marketplace/products', params={'marketplace_id': marketplace_id}, headers=get_auth_headers(buyer_token), timeout=30)
products = r.json()
print('Products:', r.status_code, json.dumps(products, indent=2, ensure_ascii=False)[:500])

# Create order
order_items = [
    {'sku_code': 'ORG-APPLE-1KG', 'quantity': '2', 'unit_price': '50000'},
    {'sku_code': 'FRESH-TOMATO-1KG', 'quantity': '3', 'unit_price': '30000'},
]
r = httpx.post(f'{API_V1}/commerce/orders', json={'items': order_items, 'shipping_address': {'city': 'Tehran', 'address': 'Buyer Address'}}, headers=get_auth_headers(buyer_token), timeout=30)
print('Create Order:', r.status_code)
if r.status_code in (200, 201):
    order = r.json()
    order_id = order.get('order_id') or order.get('id')
    print('Order ID:', order_id)
    print('Order Total:', order.get('total'))
    
    # Pay order
    r = httpx.post(f'{API_V1}/commerce/orders/{order_id}/pay', json={'provider': 'wallet'}, headers=get_auth_headers(buyer_token), timeout=30)
    print('Pay Order:', r.status_code, r.json())
    
    # Confirm payment
    r = httpx.post(f'{API_V1}/commerce/orders/{order_id}/confirm-payment', headers=get_auth_headers(buyer_token), timeout=30)
    print('Confirm Payment:', r.status_code, r.json())
    
    # Check wallets after
    r = httpx.get(f'{API_V1}/finance/wallet', headers=get_auth_headers(buyer_token), timeout=30)
    print('Buyer Wallet (after):', r.status_code, r.json())
    
    r = httpx.get(f'{API_V1}/finance/wallet', headers=get_auth_headers(seller_token), timeout=30)
    print('Seller Wallet (after):', r.status_code, r.json())
    
    # Get order detail
    r = httpx.get(f'{API_V1}/commerce/orders/{order_id}', headers=get_auth_headers(buyer_token), timeout=30)
    print('Order Detail:', r.status_code, r.json())
else:
    print('Order Error:', r.text)