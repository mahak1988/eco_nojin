#!/usr/bin/env python
"""
Integration Test: Marketplace Flow with Buyer & Seller
Tests: Seller creates marketplace/shop/products -> Buyer orders -> Payment -> Seller receives commission
"""
import asyncio
import httpx
import json
import uuid
from decimal import Decimal

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

class TestClient:
    def __init__(self, name):
        self.name = name
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.user_id = None
    
    async def close(self):
        await self.client.aclose()
    
    def _headers(self, extra=None):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        if extra:
            headers.update(extra)
        return headers
    
    async def register(self, email, password, full_name, phone=None):
        data = {
            "email": email, 
            "password": password, 
            "full_name": full_name,
            "accept_tos": True,
            "accept_privacy": True
        }
        if phone:
            data["phone"] = phone
        r = await self.client.post(f"{API_V1}/auth/register", json=data)
        print(f"[{self.name}] Register: {r.status_code}")
        if r.status_code in (200, 201):
            result = r.json()
            self.token = result.get("access_token")
            self.user_id = result.get("user_id")
            print(f"[{self.name}] Got token, User ID: {self.user_id}")
        else:
            print(f"[{self.name}] Register failed: {r.text[:200]}")
        return r
    
    async def login(self, email, password):
        data = {"email": email, "password": password}
        r = await self.client.post(f"{API_V1}/auth/login", json=data)
        print(f"[{self.name}] Login: {r.status_code}")
        if r.status_code == 200:
            self.token = r.json()["access_token"]
            me = await self.client.get(f"{API_V1}/auth/me", headers=self._headers())
            if me.status_code == 200:
                self.user_id = me.json()["id"]
                print(f"[{self.name}] User ID: {self.user_id}")
        else:
            print(f"[{self.name}] Login failed: {r.text[:200]}")
        return r
    
    def _idempotency_header(self):
        return {"Idempotency-Key": str(uuid.uuid4())}
    
    # Marketplace endpoints
    async def create_marketplace(self, name, slug, marketplace_type="local", description="", village_id=None):
        data = {"name": name, "slug": slug, "marketplace_type": marketplace_type, "description": description}
        if village_id:
            data["village_id"] = village_id
        r = await self.client.post(f"{API_V1}/marketplace/marketplaces", json=data, headers=self._headers())
        print(f"[{self.name}] Create Marketplace: {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"  Error: {r.text[:300]}")
        return r
    
    async def list_marketplaces(self):
        r = await self.client.get(f"{API_V1}/marketplace/marketplaces", headers=self._headers())
        print(f"[{self.name}] List Marketplaces: {r.status_code}")
        return r
    
    async def create_shop(self, marketplace_id, name, slug, description="", contact_info=None):
        data = {"marketplace_id": marketplace_id, "name": name, "slug": slug, "description": description}
        if contact_info:
            data["contact_info"] = contact_info
        r = await self.client.post(f"{API_V1}/marketplace/shops", json=data, headers=self._headers())
        print(f"[{self.name}] Create Shop: {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"  Error: {r.text[:300]}")
        return r
    
    async def list_shops(self, marketplace_id):
        r = await self.client.get(f"{API_V1}/marketplace/shops?marketplace_id={marketplace_id}", headers=self._headers())
        print(f"[{self.name}] List Shops: {r.status_code}")
        return r
    
    async def create_product(self, shop_id, name, sku, price, stock_qty=100, category="general", description=""):
        data = {
            "shop_id": shop_id,
            "name": name,
            "sku": sku,
            "price": str(price),
            "stock_qty": str(stock_qty),
            "category": category,
            "description": description
        }
        r = await self.client.post(f"{API_V1}/marketplace/products", json=data, headers=self._headers())
        print(f"[{self.name}] Create Product: {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"  Error: {r.text[:300]}")
        return r
    
    async def list_products(self, marketplace_id=None, shop_id=None):
        params = {}
        if marketplace_id:
            params["marketplace_id"] = marketplace_id
        if shop_id:
            params["shop_id"] = shop_id
        r = await self.client.get(f"{API_V1}/marketplace/products", params=params, headers=self._headers())
        print(f"[{self.name}] List Products: {r.status_code}")
        return r
    
    # Commerce endpoints
    async def create_order(self, items, shipping_address=None):
        data = {"items": items}
        if shipping_address:
            data["shipping_address"] = shipping_address
        r = await self.client.post(f"{API_V1}/commerce/orders", json=data, headers=self._headers())
        print(f"[{self.name}] Create Order: {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"  Error: {r.text[:300]}")
        return r
    
    async def pay_order(self, order_id, provider="wallet"):
        data = {"provider": provider}
        r = await self.client.post(f"{API_V1}/commerce/orders/{order_id}/pay", json=data, headers=self._headers())
        print(f"[{self.name}] Pay Order: {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"  Error: {r.text[:300]}")
        return r
    
    async def confirm_payment(self, order_id):
        r = await self.client.post(f"{API_V1}/commerce/orders/{order_id}/confirm-payment", headers=self._headers())
        print(f"[{self.name}] Confirm Payment: {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"  Error: {r.text[:300]}")
        return r
    
    async def get_orders(self):
        r = await self.client.get(f"{API_V1}/commerce/orders", headers=self._headers())
        print(f"[{self.name}] Get Orders: {r.status_code}")
        return r
    
    async def get_order(self, order_id):
        r = await self.client.get(f"{API_V1}/commerce/orders/{order_id}", headers=self._headers())
        print(f"[{self.name}] Get Order: {r.status_code}")
        return r
    
    # Finance/Wallet endpoints
    async def get_wallet(self):
        r = await self.client.get(f"{API_V1}/finance/wallet", headers=self._headers())
        print(f"[{self.name}] Wallet: {r.status_code}")
        return r
    
    async def earn_wallet(self, category, quantity=1):
        data = {"category": category, "quantity": str(quantity)}
        r = await self.client.post(f"{API_V1}/finance/wallet/earn", json=data, headers=self._headers(self._idempotency_header()))
        print(f"[{self.name}] Earn Wallet: {r.status_code}")
        if r.status_code not in (200, 201):
            print(f"  Error: {r.text[:300]}")
        return r


async def run_test():
    print("=" * 60)
    print("MARKETPLACE INTEGRATION TEST")
    print("=" * 60)
    
    seller = TestClient("SELLER")
    buyer = TestClient("BUYER")
    
    try:
        # ============================================================
        # STEP 1: Register Users (register returns token directly)
        # ============================================================
        print("\n--- STEP 1: User Registration ---")
        
        await seller.register("seller@test.com", "seller123", "Test Seller", "+989123456789")
        await buyer.register("buyer@test.com", "buyer123", "Test Buyer", "+989123456790")
        
        # Give buyer some wallet balance for payment
        print("\n--- Funding Buyer Wallet ---")
        await buyer.earn_wallet("education", 10)  # Earn 10 ECO credits
        bal = await buyer.get_wallet()
        print(f"Buyer Wallet: {bal.json()}")
        
        # ============================================================
        # STEP 2: Seller Creates Marketplace & Shop
        # ============================================================
        print("\n--- STEP 2: Seller Creates Marketplace & Shop ---")
        
        mp_resp = await seller.create_marketplace(
            name="Test Bazaar", 
            slug="test-bazaar", 
            marketplace_type="local",
            description="A test marketplace for integration testing"
        )
        if mp_resp.status_code not in (200, 201):
            print("Trying to list existing marketplaces...")
            list_resp = await seller.list_marketplaces()
            marketplaces_data = list_resp.json()
            marketplaces = marketplaces_data.get("marketplaces", marketplaces_data.get("items", []))
            if marketplaces:
                marketplace = marketplaces[0]
                marketplace_id = marketplace.get("id") or marketplace.get("marketplace_id")
                print(f"Using existing marketplace: {marketplace_id}")
            else:
                raise Exception("No marketplace available")
        else:
            marketplace = mp_resp.json()
            marketplace_id = marketplace.get("id") or marketplace.get("marketplace_id")
            print(f"Marketplace created: {marketplace_id}")
        
        shop_resp = await seller.create_shop(
            marketplace_id=marketplace_id,
            name="Seller's Shop",
            slug="seller-shop",
            description="Best products in town",
            contact_info={"phone": "+989123456789", "address": "Tehran, Iran"}
        )
        if shop_resp.status_code not in (200, 201):
            print("Trying to list existing shops...")
            list_resp = await seller.list_shops(marketplace_id)
            shops_data = list_resp.json()
            shops = shops_data.get("shops", shops_data.get("items", []))
            if shops:
                shop = shops[0]
                shop_id = shop.get("id") or shop.get("shop_id")
                print(f"Using existing shop: {shop_id}")
            else:
                raise Exception("No shop available")
        else:
            shop = shop_resp.json()
            shop_id = shop.get("id") or shop.get("shop_id")
            print(f"Shop created: {shop_id}")
        
        # ============================================================
        # STEP 3: Seller Creates Products
        # ============================================================
        print("\n--- STEP 3: Seller Creates Products ---")
        
        products = [
            {"name": "Organic Apples", "sku": "ORG-APPLE-1KG", "price": "50000", "stock_qty": 50, "category": "fruit"},
            {"name": "Fresh Tomatoes", "sku": "FRESH-TOMATO-1KG", "price": "30000", "stock_qty": 30, "category": "vegetable"},
            {"name": "Organic Honey", "sku": "ORG-HONEY-500G", "price": "200000", "stock_qty": 20, "category": "honey"},
        ]
        
        product_ids = []
        for p in products:
            resp = await seller.create_product(shop_id=shop_id, **p)
            if resp.status_code in (200, 201):
                prod = resp.json()
                product_ids.append({"id": prod.get("id") or prod.get("product_id"), "sku": prod.get("sku", p["sku"]), "price": p["price"]})
                print(f"  Product: {prod.get('name', p['name'])} (ID: {prod.get('id') or prod.get('product_id')}, Price: {p['price']})")
        
        # ============================================================
        # STEP 4: Buyer Browses Products
        # ============================================================
        print("\n--- STEP 4: Buyer Browses Products ---")
        
        list_resp = await buyer.list_products(marketplace_id=marketplace_id)
        products_list = list_resp.json()
        products_data = products_list.get("products", products_list.get("items", []))
        print(f"Available products: {len(products_data)}")
        for p in products_data:
            print(f"  - {p.get('name', 'N/A')}: {p.get('price', 'N/A')} (Stock: {p.get('stock_qty', 'N/A')})")
        
        # ============================================================
        # STEP 5: Buyer Places Order
        # ============================================================
        print("\n--- STEP 5: Buyer Places Order ---")
        
        order_items = [
            {"sku_code": "ORG-APPLE-1KG", "quantity": "2", "unit_price": "50000"},
            {"sku_code": "FRESH-TOMATO-1KG", "quantity": "3", "unit_price": "30000"},
        ]
        
        order_resp = await buyer.create_order(
            items=order_items,
            shipping_address={"city": "Tehran", "address": "Buyer Address", "postal_code": "12345"}
        )
        if order_resp.status_code not in (200, 201):
            print("Order creation failed!")
            return
        order = order_resp.json()
        order_id = order.get("order_id") or order.get("id")
        print(f"Order created: {order_id}")
        print(f"  Total: {order.get('total', 'N/A')}")
        print(f"  Status: {order.get('status', 'N/A')}")
        
        # ============================================================
        # STEP 6: Payment Processing
        # ============================================================
        print("\n--- STEP 6: Payment Processing ---")
        
        # Pay order using wallet
        pay_resp = await buyer.pay_order(order_id, provider="wallet")
        payment_result = pay_resp.json()
        print(f"Payment initiated: {payment_result}")
        
        # Confirm payment
        confirm_resp = await buyer.confirm_payment(order_id)
        confirm_result = confirm_resp.json()
        print(f"Payment confirmed: {confirm_result}")
        
        # ============================================================
        # STEP 7: Verify Results
        # ============================================================
        print("\n--- STEP 7: Verify Results ---")
        
        # Check buyer wallet
        bal = await buyer.get_wallet()
        print(f"Buyer Wallet After: {bal.json()}")
        
        # Check seller wallet (should have received commission)
        bal = await seller.get_wallet()
        print(f"Seller Wallet After: {bal.json()}")
        
        # Check order status
        orders = await buyer.get_orders()
        print(f"Buyer Orders: {orders.json()}")
        
        order_detail = await buyer.get_order(order_id)
        print(f"Order Detail: {order_detail.json()}")
        
        orders = await seller.get_orders()
        print(f"Seller Orders: {orders.json()}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await seller.close()
        await buyer.close()


if __name__ == "__main__":
    asyncio.run(run_test())