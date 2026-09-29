# Marketplace implementation

**Status:** Recorded from the repository at commit `2177450` on 2026-09-25. This document describes what the code does today. It does not claim that any flow listed as blocked has been implemented, and it does not record any deployment, seed data, or gateway credential as available.

Companion documents: [`PUBLIC_PAGES_EXECUTION.md`](PUBLIC_PAGES_EXECUTION.md) and [`PAGE_GATES.md`](PAGE_GATES.md). Boundary rules are in [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`../adr/0003-api-contract.md`](../adr/0003-api-contract.md).

## How to read the status column

| Status | Meaning |
|---|---|
| `live` | The page calls a gateway endpoint that exists in `openapi.json` and the response is rendered as returned. |
| `live-partial` | The page calls a real endpoint, but a declared part of the flow is unreachable or unwired in the current code. |
| `unavailable` | The page renders `market.template.unavailable*` or `statusLine.unavailable` and asserts no number or claim. |
| `static` | The page renders fixed editorial copy and makes no request. |

`unavailable` and `static` are the accepted state for a capability with no contract. They are not defects; they become defects only when a page claims data it does not have.

## Owner vocabulary

The repository has no owner registry file. The owners below are the module boundaries implied by the source paths and are the accountable names for each gate in this document.

| Owner | Scope |
|---|---|
| `marketplace-web` | `apps/web/src/app/[locale]/market/**`, `apps/web/src/lib/api/{cart,escrow,market}.ts` |
| `marketplace-api` | `services/api_gateway/routers/marketplace.py`, `services/marketplace/**` |
| `payments-api` | `services/marketplace/payments_service.py`, `services/ledger/service.py` |
| `wallet-api` | `services/api_gateway/routers/ecowallet.py` |
| `bff` | `apps/web/src/app/api/[...path]/route.ts`, `apps/web/src/lib/{bff,session}/**` |
| `i18n` | `apps/web/messages/*.json` |
| `platform-operations` | Secrets, Redis, and environment promotion |

## Route matrix

`apps/web/src/app/[locale]/market/**` contains 73 `page.tsx` files. 52 render `MarketplaceTemplatePage`. 21 carry their own implementation. The catch-all `market/[...segments]` adds 444 more template routes declared in `apps/web/src/lib/marketplace-routes.ts`.

### Route counting rule for this surface

The numbers in this section are **physical routes** and **declared fallback routes**. They are not logical page paths and not implemented pages:

- A **physical route** is a `page.tsx` file. The catch-all `market/[...segments]` is one physical route.
- A **catalog fallback** is a logical path with no dedicated file that the catch-all resolves at request time. The 444 declared template routes are 444 fallback paths, all rendered by the single catch-all file.
- A **data-bearing page** is a page that issues a request to an endpoint in `openapi.json` and renders the response.

The full four-way definition and the measurable checklist that applies to it are in [`PAGE_CHECKLIST_600.md`](PAGE_CHECKLIST_600.md). The 444 figure must never be reported as 444 implemented or live pages.

### Declared inventory partition — 2026-09-26

The marketplace surface is currently described by a four-bucket partition, recorded as declarations in [`PAGE_CHECKLIST_600.md`](PAGE_CHECKLIST_600.md) section 4:

| Bucket | Count | Meaning |
|---|---|---|
| Baseline | 10 | routes with their own implementation, as distinct from the template surface |
| Implementable orphan | 14 | physical routes with no catalog binding that are implementable without a new backend contract |
| Requiring mapping | 22 | physical routes whose logical destination is not yet determined |
| Without endpoint | 27 | logical paths with no endpoint in `openapi.json`; these render `unavailable` by rule |
| **Sum** | **73** | equals the `page.tsx` count recorded at commit `2177450` |

The partition is treated as gapless and non-overlapping, which is a working assumption rather than a verified fact, and the checklist is the instrument that verifies it. Two open items follow:

- The tree now holds 74 marketplace `page.tsx` files, so the 74th file is unassigned against the partition. Open as `R-2` in [`PAGE_CHECKLIST_600.md`](PAGE_CHECKLIST_600.md).
- `27` without endpoint is consistent with the `unavailable` rows of the matrices below, but the mapping from bucket to page is not yet written per file. Until it is, the matrices in this document remain authoritative for individual page status, and the buckets remain an inventory statement only.

### Catalog and discovery

| Page | Path | Endpoint | Status | Owner | Gate |
|---|---|---|---|---|---|
| Catalog | `/{locale}/market` | `GET /api/v1/marketplace/products`, `GET /api/v1/marketplace/stats` | `live` | `marketplace-web` | MKT-G1 |
| Product detail | `/{locale}/market/product/[id]` | `GET /api/v1/marketplace/products/{product_id}` | `live-partial` | `marketplace-web` | MKT-G2 |
| Compare | `/{locale}/market/compare` | `GET /api/v1/marketplace/products`, `GET /api/v1/marketplace/products/search` | `live` | `marketplace-web` | MKT-G1 |
| All search routes | `/{locale}/market/search/**` (11 routes) | none wired | `unavailable` | `marketplace-web` | MKT-G6 |
| Category tree | `/{locale}/market/categories/**` (4 routes) | none wired | `unavailable` | `marketplace-web` | MKT-G6 |
| Bazaar index and detail | `/{locale}/market/bazaars`, `/bazaars/[id]`, 9 `[id]/*` subroutes | none wired | `unavailable` | `marketplace-web` | MKT-G6 |
| Bazaar wizard | `/{locale}/market/bazaars/[id]/wizard` and `step1`–`step10` | `POST /api/v1/marketplace/marketplaces` (submit only) | `live-partial` | `marketplace-web` | MKT-G5 |
| Store index and detail | `/{locale}/market/stores/[id]`, `/stores/create` | none wired | `unavailable` | `marketplace-web` | MKT-G6 |
| Store creation steps | `/{locale}/market/stores/create/step1`, `step2` | none wired | `static` | `marketplace-web` | MKT-G6 |
| Catch-all generated routes | `/{locale}/market/<group>/<prefix>-<n>` (444 routes) | none wired | `unavailable` | `marketplace-web` | MKT-G6 |
| Product sub-pages | `/{locale}/market/product/[id]/{traceability,specs,similar,shipping,reviews,qa,pricing-history,eco-impact,compare,certifications,bulk,warranty}` | none wired | `unavailable` | `marketplace-web` | MKT-G6 |

### Commerce

| Page | Path | Endpoint | Status | Owner | Gate |
|---|---|---|---|---|---|
| Cart | `/{locale}/market/cart` | `GET`, `PATCH`, `DELETE /api/v1/marketplace/cart[/{product_id}]` | `live-partial` | `marketplace-web` | MKT-G3 |
| Checkout | `/{locale}/market/checkout` | `GET /cart`, `POST /orders`, `POST /payments` | `live-partial` | `marketplace-web` | MKT-G4 |
| Checkout confirmation | `/{locale}/market/checkout/confirmation` | none read | `static` | `marketplace-web` | MKT-G7 |
| Checkout step routes | `/{locale}/market/checkout/{cart-review,contract,escrow-setup,ecowallet,card,transaction-key}` | none wired | `unavailable` | `marketplace-web` | MKT-G6 |
| Orders index | `/{locale}/market/orders` | none wired | `unavailable` | `marketplace-web` | MKT-G6 |
| Order detail routes | `/{locale}/market/orders/[id]/{tracking,timeline,evidence,dispute}` | none wired | `unavailable` | `marketplace-web` | MKT-G6 |
| Escrow detail | `/{locale}/market/escrow/[id]` | `GET /api/v1/marketplace/payments/{payment_id}/escrow` | `live-partial` | `marketplace-web` | MKT-G4 |
| Wallet | `/{locale}/market/wallet` | `GET /api/v1/ecowallet/wallet/{user_id}`, `GET /api/v1/ecowallet/earnings` | `live-partial` | `marketplace-web` | MKT-G8 |

## Cart to order to payment to escrow

The intended flow is: add a product to the cart, create an order, create a payment, verify the payment so funds move into escrow hold, then settle or dispute and complete. This is what the code attempts. The following is the flow as it executes, with the divergence at each step.

```text
product/[id]  --query string-->  cart  --getCart-->  checkout
                                                   |
                            POST /orders (once per cart line)
                                                   |
                            POST /payments (once per order)
                                                   |
                            X  flow stops here
```

### Step 1 — product to cart: not connected

`apps/web/src/app/[locale]/market/product/[id]/page.tsx:121` builds `/{locale}/market/cart?product=&variant=&qty=` and navigates. The cart page never reads those parameters, and `addToCart` in `apps/web/src/lib/api/cart.ts:41` is exported but has no caller anywhere in `apps/web/src`. The `POST /api/v1/marketplace/cart` endpoint exists and is declared in `openapi.json`, so this is a frontend-only gap.

### Step 2 — cart: live, write-capable

`apps/web/src/app/[locale]/market/cart/page.tsx` reads the cart through `getCart()` and writes through `updateCartItem` and `removeFromCart`. All three endpoints require a bearer token in `openapi.json`, and the page gates on `useAuth()`. Fees are computed in the browser at 5% platform and 2% escrow (`market/cart/page.tsx:35`). These rates are not returned by any endpoint, so the displayed total is a frontend constant.

### Step 3 — order creation: live, with an accounting mismatch

`apps/web/src/app/[locale]/market/checkout/page.tsx:104` issues one `POST /api/v1/marketplace/orders` per cart line, so a three-line cart becomes three orders. The request carries `product_id`, `buyer_name`, and `quantity_kg`; there is no cart identifier, so the backend cannot group the lines.

The cart is not cleared after the orders are created. A second submit creates a second set of orders, and the idempotency key is regenerated on every attempt (`apps/web/src/lib/api/client.ts:29`).

### Step 4 — payment creation: blocked on the gateway allow-list

This is the hard stop in the current code.

| Layer | Value |
|---|---|
| `openapi.json` `PaymentRequest.payment_method` | free-form `string`, default `"bank"`, no enum |
| `services/marketplace/payments_service.py:32` `VALID_GATEWAYS` | `("zarinpal", "bank", "international")` |
| `apps/web/src/lib/api/escrow.ts:8` `CreatePaymentRequest.paymentMethod` | `'ecowallet' \| 'bank' \| 'card'` |
| `apps/web/src/app/[locale]/market/checkout/page.tsx:305` submit button | enabled only when `walletSelected === 'ecowallet'` |

`ecowallet` and `card` are not in `VALID_GATEWAYS`, so `POST /api/v1/marketplace/payments` raises `PaymentError("unknown gateway")` and returns HTTP 400. Selecting `card` disables the button instead of sending it. Both branches of the payment selector therefore fail, and the confirmation step is unreachable.

Separately, the amount sent is `price × quantity` per line (`checkout/page.tsx:124`), which is the line subtotal. The total shown to the buyer includes the 5% and 2% fees. The charged amount and the displayed amount are not the same number.

### Step 5 — escrow hold: never reached from the browser

`confirmPayment` in `apps/web/src/lib/api/escrow.ts:59` is exported and has no caller. `POST /api/v1/marketplace/payments/{payment_id}/confirm` is the only endpoint that calls `EscrowService.hold` and creates a `MarketplaceEscrowEntry` row (`services/marketplace/payments_service.py:171`). Because the browser never calls it, no escrow hold is ever created by the web flow, and `GET /payments/{payment_id}/escrow` returns an empty ledger for web-created orders.

### Step 6 — dispute, settle, complete: two disjoint escrow models

The repository contains two escrow implementations that do not share a table.

| Operation | Service | Table | Auth |
|---|---|---|---|
| `POST /payments/{payment_id}/confirm` | `services.marketplace.payments_service.EscrowService` | `MarketplaceEscrowEntry` | `require_user` |
| `GET /payments/{payment_id}/escrow` | `services.marketplace.payments_service.EscrowService` | `MarketplaceEscrowEntry` | `require_user` |
| `POST /payments/{payment_id}/escrow/release` | `services.marketplace.payments_service.EscrowService` | `MarketplaceEscrowEntry` | `require_admin` |
| `POST /payments/{payment_id}/escrow/refund` | `services.marketplace.payments_service.EscrowService` | `MarketplaceEscrowEntry` | `require_admin` |
| `POST /orders/{order_id}/dispute` | `services.ledger.service.EscrowService` | `EscrowRecord` | `require_user` |
| `POST /orders/{order_id}/settle` | `services.ledger.service.EscrowService` | `EscrowRecord` | `require_user` |
| `POST /orders/{order_id}/complete` | `services.ledger.service.EscrowService` | `EscrowRecord` | `require_user` |

The three `orders/{order_id}` transitions look up an `EscrowRecord` row, which nothing in the marketplace payment path creates. `complete` raises `LookupError("No escrow for order ...")` and returns HTTP 404. The two families also disagree on authority: releasing funds by payment id requires an administrator, while settling by order id requires any authenticated user.

`completeOrder` in `apps/web/src/lib/api/escrow.ts:80` is exported and has no caller.

### Step 7 — escrow page controls: permanently disabled

`apps/web/src/app/[locale]/market/escrow/[id]/page.tsx:86` copies only `escrow_status` out of the response. `orderId` is left at the `EMPTY_ESCROW` value of `''`, so the release and dispute buttons are disabled at `escrow/[id]/page.tsx:246` and `escrow/[id]/page.tsx:251`. The dispute and settle calls at lines 109 and 122 are unreachable from the page. The amount, parties, events, and contract hash panels render their empty defaults.

## Wallet page

`apps/web/src/app/[locale]/market/wallet/page.tsx` reads `/api/v1/ecowallet/wallet/{user_id}` and `/api/v1/ecowallet/earnings?user_id=`, passing the user id held in the client session. Three defects are visible in the current code:

1. **Unit mismatch.** The response is an EcoCoin balance; the page sets `currency: 'ECO'` and renders the value with a `ریال` suffix on lines 171, 178, and 196.
2. **Reserved amount is not reserved.** `reserved` is bound to `total_redeemed` (line 89), a cumulative redemption figure, and `available` is computed as `balance - reserved` (line 94). The available figure can go negative and is not a spendable balance.
3. **Withdrawal is not implemented.** `handleWithdraw` only sets an error string, and `isWithdrawing` is the constant `false` (line 69).

The two endpoints this page depends on have no `require_user` dependency in `services/api_gateway/routers/ecowallet.py:208` and `:218`. Any caller can read any wallet by supplying an arbitrary `user_id`. This is recorded as blocker B2 in [`PAGE_GATES.md`](PAGE_GATES.md); it is a backend change and is out of scope for this document.

## Unauthenticated reads on the commerce surface

Two commerce reads carry no `require_user` dependency in `services/api_gateway/routers/marketplace.py`, and `openapi.json` declares no security requirement for them:

| Endpoint | Returns | Source |
|---|---|---|
| `GET /api/v1/marketplace/orders` | every order with `buyer_name`, amounts, and status | `marketplace.py:311` |
| `GET /api/v1/marketplace/orders/{order_id}/track` | the tracking timeline for any order id | `marketplace.py:350` |

The orders and order-detail pages in the web app are `unavailable` and do not call them, so the browser does not currently expose the data. The finding is recorded so that the "needs new API" work in this document does not build a page on top of an open endpoint. Recorded as blocker B1.

## Completable without a backend change

These are frontend-only. Each one uses an endpoint that already exists in `openapi.json`.

| Item | Work | Gate |
|---|---|---|
| Product add-to-cart | Call the existing `addToCart` on the product page instead of navigating with query parameters; make the cart page accept a deep link | MKT-G3 |
| Cart clearing | Remove purchased lines after order creation | MKT-G3 |
| Idempotent retry | Reuse one `Idempotency-Key` across retries of the same submit | MKT-G4 |
| Payment selector | Send a gateway from `VALID_GATEWAYS`; `bank` is reachable with no merchant configuration, `zarinpal` and `international` are not | MKT-G4 |
| Payment confirmation | Call the existing `confirmPayment` so the escrow hold is created | MKT-G4 |
| Escrow page | Read `payment_id` and derive the order id, or add an order id to the escrow response, so the release and dispute controls are reachable | MKT-G4 |
| Fee model | Either move the fee rates to an endpoint or label the displayed total as an estimate | MKT-G3 |
| Wallet truthfulness | Show the EcoCoin unit, stop deriving `available` from `total_redeemed`, and remove the withdrawal form until an endpoint exists | MKT-G8 |
| Product sub-pages | Bind the twelve `unavailable` product sub-pages to `GET /products/{product_id}` and `GET /products/{product_id}/trace` where the response carries the field | MKT-G2 |
| Search | Bind `market/search` to the existing `GET /products/search` and `GET /products` with the existing `category`, `min_price`, `max_price`, and `limit` query parameters | MKT-G6 |
| Bazaar wizard | The submit already posts to `POST /marketplaces`; the ten step routes need no endpoint of their own | MKT-G5 |
| Contract drift | `apps/web/src/lib/domains/registry.ts:102` declares `/api/v1/tool-registry/{toolId}`; `openapi.json` declares `/api/v1/tool-registry/{tool_id}` | MKT-G9 |

## Requires a new or changed backend API

| Item | Required change | Gate |
|---|---|---|
| EcoCoin and card payment | Either extend `VALID_GATEWAYS` with `ecowallet` and `card`, or change the web selector to `zarinpal`, `bank`, `international`. Add an enum to `PaymentRequest.payment_method` so the three layers cannot disagree again | MKT-G4 |
| Escrow amount | Return the amount that will be held, or return a server-computed total that includes the fees, so the charged amount matches the displayed amount | MKT-G4 |
| Single order per checkout | Accept the cart identifier so a multi-line cart produces one order, and clear the cart server-side | MKT-G4 |
| Escrow model unification | Decide which escrow implementation is canonical, or have the payment confirmation create the `EscrowRecord` that the `orders/{order_id}` transitions read | MKT-G4 |
| Escrow authority | Make the release path consistent: an order-scoped settle by the seller, or an admin-only release, but one rule applied to both routes | MKT-G4 |
| Wallet ownership | Derive `user_id` from the authenticated session instead of a query parameter | MKT-G8 |
| Wallet withdrawal | A redemption or transfer endpoint; `POST /api/v1/ecowallet/redeem` and `/transfer` exist but are not a wallet-withdrawal contract | MKT-G8 |
| Bazaar detail and settings | Read endpoints for a single marketplace, its shops, and its members, behind the roles the wizard already implies | MKT-G6 |
| Store detail | A store or vendor projection; `GET /vendors`, `/vendors/{id}`, and `/vendors/{id}/products` exist but expose sellers, not storefronts | MKT-G6 |
| Category tree | A category read model; `GET /marketplace/products` accepts a `category` filter but there is no category resource | MKT-G6 |
| Order list and detail for the buyer | A buyer-scoped order list, or authentication on the existing one, before `market/orders` is promoted from `unavailable` | MKT-G6 |
| Dispute window and completion | The `remaining_seconds` field is already returned by `dispute`; `complete` needs a reachable `EscrowRecord` | MKT-G4 |
| Fee schedule | A fee or pricing endpoint if the 5% and 2% rates are to be shown as authoritative | MKT-G3 |

## Acceptance criteria

- **MKT-G1 catalog.** A rendered product count equals the count in the `GET /products` response. No count appears when the request fails; the `unavailable` message is shown instead.
- **MKT-G2 product detail.** Add to cart performs a `POST /cart` and the cart page reflects the new line on reload. No navigation with an unparsed query string.
- **MKT-G3 cart.** Quantity change and removal persist through the API and survive a reload. The displayed total is either server-computed or labelled as an estimate. A submitted cart is emptied.
- **MKT-G4 payment and escrow.** A payment is created with a gateway in `VALID_GATEWAYS`, the confirm call runs, `GET /payments/{id}/escrow` returns at least one entry afterwards, and the amount held equals the amount displayed at checkout. The dispute and settle controls are reachable and return the documented status codes.
- **MKT-G5 bazaar wizard.** The ten steps complete and submit once. A duplicate submit with the same idempotency key does not create a second marketplace.
- **MKT-G6 unavailable routes.** Every route in this group still renders `unavailable`, carries `robots: noindex`, and shows no number, date, or partner name that is not returned by a live call.
- **MKT-G7 checkout confirmation.** The page states no transaction key, escrow amount, or dispute window unless it is given one. It is not reachable by a bare URL with invented values.
- **MKT-G8 wallet.** The balance is labelled in EcoCoin. The available figure comes from a field the API defines as spendable. No withdrawal control is shown without a withdrawal endpoint.
- **MKT-G9 contract drift.** The endpoint strings in `apps/web/src/lib/domains/registry.ts` match `openapi.json` path templates exactly.

## Definition of Done for the marketplace surface

1. Every page in the route matrix has a status in this document that matches what the code renders.
2. Every `live-partial` entry has become `live` or has been moved to the requires-new-API table with an owner.
3. The cart-to-escrow path completes end to end against a local gateway with real rows in the database, verified by an integration test, not by a screenshot.
4. No frontend page hard-codes a currency, fee rate, escrow window, or transaction identifier.
5. `openapi.json` is regenerated and the generated client drift check passes.
6. The full quality gate in [`TESTING.md`](TESTING.md) is green on the same commit, including the auth, money, and state-machine coverage that this document's flows require.
7. Blockers B1 and B2 in [`PAGE_GATES.md`](PAGE_GATES.md) are either fixed or accepted in writing by the security owner. The marketplace flow is not declared done while they are open.

## External blockers

These are not frontend work and are not resolved by any change in `apps/web`.

| ID | Blocker | Owner |
|---|---|---|
| B1 | `GET /marketplace/orders` and `GET /marketplace/orders/{order_id}/track` have no authentication | `marketplace-api`, security owner |
| B2 | `GET /ecowallet/wallet/{user_id}` and `GET /ecowallet/earnings` accept an unauthenticated arbitrary user id | `wallet-api`, security owner |
| B3 | The two escrow implementations read different tables, so `orders/{order_id}/settle` and `/complete` cannot succeed for a marketplace payment | `payments-api` |
| B4 | `zarinpal` requires `ZARINPAL_MERCHANT_ID`; `international` requires `INTL_PAYMENT_CHECKOUT_URL`. Neither is present in the repository, so only `bank` is reachable | `platform-operations` |
| B5 | `REDIS_URL` is required in production and must be supplied by a cluster secret; the value is not in the repository | `platform-operations` |

## Execution result — 2026-09-25

- cart, checkout, product detail, compare, wallet, and escrow pages now use real session-aware API clients and honest state components.
- payment gateways are limited to `zarinpal`, `bank`, and `international`, matching the gateway contract.
- checkout creates orders sequentially, charges the server-returned `total_price`, clears purchased cart lines, and links escrow with the real `order` query.
- the marketplace list and detail pages read `/api/v1/marketplace/marketplaces`; a validated, authenticated creation form posts to the same collection with an idempotency key.
- the wallet uses the gateway's `balance`, `total_earned`, `total_redeemed`, and `is_active` fields and does not display an available figure the API does not define.
- placeholder wizard, store-step, and checkout-confirmation routes remain explicitly unavailable.
- B1–B5 remain external; the frontend no longer hides them behind synthetic success states.

## Inventory note — 2026-09-26

- the marketplace surface measures 74 `page.tsx` files today against the 73 recorded at `2177450`; the delta is stated in [`PAGE_GATES.md`](PAGE_GATES.md) rather than rewritten here, so the 2026-09-25 record stays intact.
- the four-bucket partition (10 baseline, 14 implementable orphan, 22 requiring mapping, 27 without endpoint) is recorded above. Its sum of 73 is one below the current measured 74, and the 74th file is unassigned.
- nothing in this note changes a page status, a gate, or a blocker. The route matrices in this document remain authoritative for individual pages; the buckets are inventory only.

## Cluster status — 2026-09-29

The marketplace agent (`docs/frontend/agents/agent-4-marketplace.md`) processes one cluster of [`CONTRACT_REQUEST_154.md`](CONTRACT_REQUEST_154.md) per run and either binds the cluster's routes to live endpoints or records the cluster as `awaiting contract`. This run processed `market/bazaars`.

| Check (2026-09-29) | Result |
|---|---|
| Requested endpoints | 19 — `/market/bazaars/{id}/analytics`, `/disputes`, `/finances`, `/governance`, `/map`, `/settings`, `/stores`, `/supervision`, `/wizard`, `/wizard/step1` … `/wizard/step10` |
| Running gateway `openapi.json` | 0 / 19 paths present |
| Repository `openapi.json` | 0 / 19 paths present |
| Page-catalogue declarations | all `endpoint: null` (consistent) |
| **Status** | **`awaiting contract`** («منتظر قرارداد») |

**Page states at this check (no page was changed by this run).** `/{locale}/market/bazaars` and `/{locale}/market/bazaars/{id}` read the published `GET /api/v1/marketplace/marketplaces[/{marketplace_id}]`; `/{locale}/market/bazaars/create` posts to the same collection. The nineteen `{id}/*` routes keep honest states — the seven template routes render the route and its unavailable status, and the map, wizard and ten step routes render their purpose-built states and post nothing. MKT-G6 holds for these routes: noindex, and no number, date, or partner name that is not returned by a live call.

**Queue.** Remaining clusters for later runs: `market/product`, `market/search`, `market/categories`, `market/stores`. Each will be recorded here when its run completes.
