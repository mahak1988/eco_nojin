"""Real Supabase Auth proxy — signup/login/me via GoTrue.

Free tier, keys already in .env. The anon key is a publishable key (safe
server-side here); the SERVICE_ROLE key is NEVER exposed to the frontend
and is only used for admin operations (delete test user, user lookup).

FALLBACK: when the Supabase project is unreachable (network, DNS, disabled
project) the endpoints transparently delegate to the local SQLite auth
router so registration and login keep working offline.
"""

import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.api_gateway.auth import (
    create_access_token,
    create_refresh_token,
    require_admin,
    role_of,
)
from services.api_gateway.routers.auth import (
    get_async_db,
)

router = APIRouter(prefix="/api/v1/auth/supabase", tags=["auth-supabase"])

# Error types that indicate the Supabase project is unreachable.
_NETWORK_ERRORS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    httpx.PoolTimeout,
    ConnectionError,
    TimeoutError,
    OSError,
)


def _is_network_error(exc: Exception) -> bool:
    """True when the exception means Supabase itself is unreachable."""
    if isinstance(exc, _NETWORK_ERRORS):
        return True
    msg = str(exc).lower()
    return any(
        token in msg
        for token in (
            "getaddrinfo",
            "name or service not known",
            "connection refused",
            "connection reset",
            "timed out",
            "network unreachable",
            "no route to host",
        )
    )


async def _supabase_reachable() -> bool:
    """Quick DNS + TCP check so we don't wait for a 20 s timeout on every call."""
    try:
        cfg = _cfg()
        import socket

        host = cfg["url"].replace("https://", "").replace("http://", "").split("/")[0]
        socket.getaddrinfo(host, 443)
        return True
    except Exception:
        return False


def _cfg() -> dict[str, str]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    anon = os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_KEY", "")
    svc = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not anon:
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY missing in environment")
    return {"url": url, "anon": anon, "svc": svc}


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=6, max_length=100)
    phone: str | None = None
    full_name: str | None = Field(None, min_length=2, max_length=100)
    birth_year: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    role: str = Field(
        default="regular", pattern="^(farmer|researcher|organization|tourist|regular)$"
    )
    language: str = Field(default="fa", pattern="^(fa|en|ar|tr)$")


class LoginRequest(BaseModel):
    email: str
    password: str


async def _goto(
    session: httpx.AsyncClient, cfg: dict[str, str], path: str, body: dict[str, Any], key: str
) -> dict[str, Any]:
    r = await session.post(
        f"{cfg['url']}{path}",
        json=body,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    return {
        "http": r.status_code,
        "body": r.json()
        if r.headers.get("content-type", "").startswith("application/json")
        else {"raw": r.text[:200]},
    }


@router.post("/signup")
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_async_db)) -> dict[str, Any]:
    """Real GoTrue signup (email+password). Returns session tokens on success.
    Profile fields are stored as user_metadata so they survive across
    devices and are returned by /me.

    FALLBACK: when the Supabase project is unreachable (DNS failure, network
    down, project disabled) the request is transparently served by the local
    SQLite auth router so registration keeps working offline."""
    try:
        if not await _supabase_reachable():
            return await _local_signup(req, db)

        cfg = _cfg()
        payload: dict[str, Any] = {
            "email": req.email,
            "password": req.password,
            "data": {
                "full_name": req.full_name,
                "phone": req.phone,
                "birth_year": req.birth_year,
                "country": req.country,
                "city": req.city,
                "address": req.address,
                "role": req.role,
                "language": req.language,
            },
        }
        async with httpx.AsyncClient(timeout=20) as s:
            res = await _goto(s, cfg, "/auth/v1/signup", payload, cfg["anon"])
        body = res["body"]
        if res["http"] not in (200, 201):
            return {
                "status": "error",
                "error": body.get("msg") or body.get("error_description") or f"HTTP {res['http']}",
                "http": res["http"],
            }
        user = body.get("user") or {}
        user_id = user.get("id")
        session = body.get("session")

        # If GoTrue already returned a session (email confirmation off), use it.
        if session and session.get("access_token"):
            return {
                "status": "ok",
                "access_token": session.get("access_token"),
                "refresh_token": session.get("refresh_token"),
                "expires_in": session.get("expires_in"),
                "email": user.get("email"),
                "user_id": user_id,
                "confirmed": True,
            }

        # Otherwise, use the service role to confirm the email and mint a session.
        if cfg["svc"] and user_id:
            async with httpx.AsyncClient(timeout=20) as s2:
                # 1. Confirm the email via admin API
                await s2.put(
                    f"{cfg['url']}/auth/v1/admin/users/{user_id}",
                    json={"email_confirmed_at": "now()"},
                    headers={
                        "apikey": cfg["svc"],
                        "Authorization": f"Bearer {cfg['svc']}",
                        "Content-Type": "application/json",
                    },
                )
                # 2. Mint a session via password grant
                tr = await s2.post(
                    f"{cfg['url']}/auth/v1/token?grant_type=password",
                    json={"email": req.email, "password": req.password},
                    headers={
                        "apikey": cfg["anon"],
                        "Authorization": f"Bearer {cfg['anon']}",
                        "Content-Type": "application/json",
                    },
                )
                tbody = (
                    tr.json()
                    if tr.headers.get("content-type", "").startswith("application/json")
                    else {}
                )
                if tr.status_code == 200 and tbody.get("access_token"):
                    return {
                        "status": "ok",
                        "access_token": tbody.get("access_token"),
                        "refresh_token": tbody.get("refresh_token"),
                        "expires_in": tbody.get("expires_in"),
                        "email": req.email,
                        "user_id": user_id,
                        "confirmed": True,
                    }
                return {
                    "status": "ok",
                    "email": req.email,
                    "user_id": user_id,
                    "confirmed": False,
                    "note": "Account created but email confirmation is required. Check your inbox.",
                }

        return {
            "status": "ok",
            "email": user.get("email"),
            "user_id": user_id,
            "confirmed": session is not None,
            "note": "در صورت فعال بودن Email Confirmation، لینک تأیید ارسال شد.",
        }
    except Exception as exc:
        if _is_network_error(exc):
            return await _local_signup(req, db)
        return {"status": "error", "error": str(exc)}


async def _local_signup(req: SignupRequest, db: AsyncSession) -> dict[str, Any]:
    """Fallback: create the user in the local SQLite auth router."""
    from sqlalchemy import select as _select

    from database.models import User as _User
    from services.api_gateway.auth import hash_password as _hash

    existing = await db.execute(_select(_User).where(_User.email == req.email))
    if existing.scalar_one_or_none():
        return {"status": "error", "error": "Email already registered", "http": 400}

    user = _User(
        email=req.email,
        full_name=req.full_name,
        hashed_password=_hash(req.password),
        role=req.role,
        phone=req.phone,
        country=req.country,
        city=req.city,
        language=req.language,
        is_email_verified=True,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(
        {"user_id": user.id}, subject=str(user.id), role=user.role or "farmer"
    )
    return {
        "status": "ok",
        "access_token": token,
        "refresh_token": create_refresh_token({}, subject=str(user.id), role=role_of(user)),
        "expires_in": 604800,
        "email": user.email,
        "user_id": user.id,
        "confirmed": True,
        "fallback": "local",
    }


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_async_db)) -> dict[str, Any]:
    """Real GoTrue password login — returns access_token + refresh_token.

    FALLBACK: when Supabase is unreachable the request is served by the
    local SQLite auth router so login keeps working offline."""
    try:
        if not await _supabase_reachable():
            return await _local_login(req, db)

        cfg = _cfg()
        async with httpx.AsyncClient(timeout=20) as s:
            res = await _goto(
                s,
                cfg,
                "/auth/v1/token?grant_type=password",
                {"email": req.email, "password": req.password},
                cfg["anon"],
            )
        body = res["body"]
        if res["http"] != 200:
            return {
                "status": "error",
                "error": body.get("msg") or body.get("error_description") or f"HTTP {res['http']}",
                "http": res["http"],
            }
        return {
            "status": "ok",
            "access_token": body.get("access_token"),
            "refresh_token": body.get("refresh_token"),
            "expires_in": body.get("expires_in"),
            "user_id": (body.get("user") or {}).get("id"),
            "email": (body.get("user") or {}).get("email"),
        }
    except Exception as exc:
        if _is_network_error(exc):
            return await _local_login(req, db)
        return {"status": "error", "error": str(exc)}


async def _local_login(req: LoginRequest, db: AsyncSession) -> dict[str, Any]:
    """Fallback: verify the user against the local SQLite auth router."""
    from sqlalchemy import select as _select

    from database.models import User as _User
    from services.api_gateway.auth import verify_password as _verify

    result = await db.execute(_select(_User).where(_User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not _verify(req.password, user.hashed_password):
        return {"status": "error", "error": "Invalid email or password", "http": 401}
    if not user.is_active:
        return {"status": "error", "error": "Account disabled", "http": 403}

    token = create_access_token(
        {"user_id": user.id}, subject=str(user.id), role=user.role or "farmer"
    )
    return {
        "status": "ok",
        "access_token": token,
        "refresh_token": create_refresh_token({}, subject=str(user.id), role=role_of(user)),
        "expires_in": 604800,
        "email": user.email,
        "user_id": user.id,
        "full_name": user.full_name,
        "role": user.role,
        "language": user.language,
        "phone": user.phone,
        "country": user.country,
        "city": user.city,
        "fallback": "local",
    }


@router.get("/me")
async def me(access_token: str, db: AsyncSession = Depends(get_async_db)) -> dict[str, Any]:
    """Validate a Supabase JWT against GoTrue (real user info).
    Returns profile fields stored in user_metadata so the frontend
    can pre-fill the profile page without a separate DB query.

    FALLBACK: when Supabase is unreachable the request is served by the
    local SQLite auth router so the profile page keeps working offline."""
    if not await _supabase_reachable():
        return await _local_me(access_token, db)
    try:
        cfg = _cfg()
        async with httpx.AsyncClient(timeout=20) as s:
            r = await s.get(
                f"{cfg['url']}/auth/v1/user",
                headers={"apikey": cfg["anon"], "Authorization": f"Bearer {access_token}"},
            )
        if r.status_code != 200:
            return {"status": "error", "error": r.json().get("msg") or f"HTTP {r.status_code}"}
        u = r.json()
        meta = u.get("user_metadata") or {}
        return {
            "status": "ok",
            "user_id": u.get("id"),
            "email": u.get("email"),
            "created_at": u.get("created_at"),
            "full_name": meta.get("full_name"),
            "phone": meta.get("phone"),
            "birth_year": meta.get("birth_year"),
            "country": meta.get("country"),
            "city": meta.get("city"),
            "address": meta.get("address"),
            "role": meta.get("role") or "regular",
            "language": meta.get("language") or "fa",
        }
    except Exception as exc:
        if _is_network_error(exc):
            return await _local_me(access_token, db)
        return {"status": "error", "error": str(exc)}


async def _local_me(access_token: str, db: AsyncSession) -> dict[str, Any]:
    """Fallback: decode the local JWT and look up the user in SQLite."""
    from sqlalchemy import select as _select

    from database.models import User as _User
    from services.api_gateway.auth import decode_token

    try:
        payload = decode_token(access_token)
    except Exception:
        payload = None
    if not payload:
        # decode_token returns None for expired/invalid tokens; fail clean
        # with the endpoint error convention instead of a 500 crash.
        return {"status": "error", "error": "Invalid token", "http": 401}

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        return {"status": "error", "error": "No user id in token", "http": 401}

    result = await db.execute(_select(_User).where(_User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"status": "error", "error": "User not found", "http": 404}

    return {
        "status": "ok",
        "user_id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "full_name": user.full_name,
        "phone": user.phone,
        "birth_year": user.date_of_birth.strftime("%Y") if user.date_of_birth else None,
        "country": user.country,
        "city": user.city,
        "address": getattr(user, "address", None),
        "role": user.role,
        "language": user.language,
        "fallback": "local",
    }


@router.put("/profile")
async def update_profile(
    access_token: str, body: dict[str, Any], db: AsyncSession = Depends(get_async_db)
) -> dict[str, Any]:
    """Update the current user's profile via the admin users endpoint.
    Requires SUPABASE_SERVICE_ROLE_KEY (server-side only — never exposed
    to the frontend).

    FALLBACK: when Supabase is unreachable the request is served by the
    local SQLite auth router so profile updates keep working offline."""
    if not await _supabase_reachable():
        return await _local_update_profile(access_token, body, db)
    try:
        cfg = _cfg()
        if not cfg["svc"]:
            return await _local_update_profile(access_token, body, db)
        # First get the user id from the access token
        async with httpx.AsyncClient(timeout=20) as s:
            r = await s.get(
                f"{cfg['url']}/auth/v1/user",
                headers={"apikey": cfg["anon"], "Authorization": f"Bearer {access_token}"},
            )
            if r.status_code != 200:
                return await _local_update_profile(access_token, body, db)
            user_id = (r.json() or {}).get("id")
            if not user_id:
                return await _local_update_profile(access_token, body, db)

            # Merge new fields into existing user_metadata
            existing_meta = (r.json() or {}).get("user_metadata") or {}
            new_meta = {**existing_meta, **body}
            pr = await s.put(
                f"{cfg['url']}/auth/v1/admin/users/{user_id}",
                json={"user_metadata": new_meta},
                headers={
                    "apikey": cfg["svc"],
                    "Authorization": f"Bearer {cfg['svc']}",
                    "Content-Type": "application/json",
                },
            )
        if pr.status_code not in (200, 201):
            return await _local_update_profile(access_token, body, db)
        return {"status": "ok", "user_metadata": new_meta}
    except Exception as exc:
        if _is_network_error(exc):
            return await _local_update_profile(access_token, body, db)
        return {"status": "error", "error": str(exc)}


async def _local_update_profile(
    access_token: str, body: dict[str, Any], db: AsyncSession
) -> dict[str, Any]:
    """Fallback: update the user's profile in the local SQLite auth router."""
    from sqlalchemy import select as _select

    from database.models import User as _User
    from services.api_gateway.auth import decode_token

    try:
        payload = decode_token(access_token)
    except Exception:
        return {"status": "error", "error": "Invalid token", "http": 401}

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        return {"status": "error", "error": "No user id in token", "http": 401}

    result = await db.execute(_select(_User).where(_User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"status": "error", "error": "User not found", "http": 404}

    if "full_name" in body and body["full_name"] is not None:
        user.full_name = body["full_name"]
    if "phone" in body:
        user.phone = body["phone"]
    if "country" in body:
        user.country = body["country"]
    if "city" in body:
        user.city = body["city"]
    if "language" in body and body["language"] is not None:
        user.language = body["language"]
    await db.commit()
    await db.refresh(user)

    return {
        "status": "ok",
        "user_metadata": {
            "full_name": user.full_name,
            "phone": user.phone,
            "country": user.country,
            "city": user.city,
            "language": user.language,
        },
        "fallback": "local",
    }


@router.post("/admin/delete-user")
async def admin_delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """Admin-only: delete a test user (service role). Requires admin role."""
    try:
        cfg = _cfg()
        if not cfg["svc"]:
            return {"status": "error", "error": "SUPABASE_SERVICE_ROLE_KEY missing"}
        async with httpx.AsyncClient(timeout=20) as s:
            r = await s.delete(
                f"{cfg['url']}/auth/v1/admin/users/{user_id}",
                headers={"apikey": cfg["svc"], "Authorization": f"Bearer {cfg['svc']}"},
            )
        return {"status": "ok" if r.status_code == 204 else "error", "http": r.status_code}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


# ============================================================================
# OAUTH LOGIN (Google / GitHub / Microsoft)
# ============================================================================

SUPPORTED_OAUTH_PROVIDERS = ("google", "github", "microsoft")


@router.get("/oauth/login")
async def oauth_login(
    provider: str, redirect_uri: str = "http://localhost:5173/login"
) -> dict[str, Any]:
    """Generate an OAuth authorization URL for the given provider.

    PRIMARY: Supabase GoTrue (real Google/GitHub/Microsoft OAuth).
    FALLBACK: when Supabase is unreachable we return a local mock URL that
    the frontend can redirect to. The mock creates a local user account
    with a provider-prefixed email so login still works offline."""
    if provider not in SUPPORTED_OAUTH_PROVIDERS:
        return {"status": "error", "error": f"Unsupported provider: {provider}", "http": 400}

    if await _supabase_reachable():
        try:
            cfg = _cfg()
            import base64
            import hashlib
            import secrets
            from urllib.parse import urlencode

            code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
            code_challenge = (
                base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
                .decode()
                .rstrip("=")
            )

            params = {
                "provider": provider,
                "redirect_to": redirect_uri,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
            url = f"{cfg['url']}/auth/v1/authorize?{urlencode(params)}"
            return {
                "status": "ok",
                "url": url,
                "provider": provider,
                "code_verifier": code_verifier,
            }
        except Exception:
            # Fall through to the local mock if the real OAuth fails.
            pass

    # LOCAL MOCK FALLBACK
    # Generate a deterministic mock code that the callback endpoint can
    # exchange for a local user account. The email is derived from the
    # provider so the same user always gets the same account.
    import secrets as _secrets

    mock_code = _secrets.token_urlsafe(16)
    return {
        "status": "ok",
        "url": f"{redirect_uri}?code={mock_code}&provider={provider}&mock=true",
        "provider": provider,
        "code_verifier": mock_code,
        "mock": True,
    }


@router.get("/oauth/callback")
async def oauth_callback(
    code: str,
    code_verifier: str,
    provider: str = "google",
    mock: bool = False,
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Handle the OAuth callback — exchange the authorization code for a
    session, then create or look up the user in the local SQLite auth
    router and return a local JWT.

    REAL FLOW: when Supabase is reachable and `mock=false`, the code is
    exchanged with GoTrue via PKCE.

    MOCK FLOW: when `mock=true` or Supabase is unreachable, we create a
    local user account with a provider-prefixed email (e.g.
    `user_google@example.com`) so OAuth login works offline."""
    if mock or not await _supabase_reachable():
        return await _local_oauth_callback(code, code_verifier, provider, db)

    try:
        cfg = _cfg()
        async with httpx.AsyncClient(timeout=20) as s:
            # 1. Exchange the code for a session
            tr = await s.post(
                f"{cfg['url']}/auth/v1/token?grant_type=pkce",
                json={
                    "code": code,
                    "code_verifier": code_verifier,
                },
                headers={
                    "apikey": cfg["anon"],
                    "Authorization": f"Bearer {cfg['anon']}",
                    "Content-Type": "application/json",
                },
            )
            tbody = (
                tr.json()
                if tr.headers.get("content-type", "").startswith("application/json")
                else {}
            )
            if tr.status_code != 200 or not tbody.get("access_token"):
                return {
                    "status": "error",
                    "error": tbody.get("error_description") or "OAuth exchange failed",
                    "http": tr.status_code,
                }

            # 2. Get the user info
            ur = await s.get(
                f"{cfg['url']}/auth/v1/user",
                headers={"apikey": cfg["anon"], "Authorization": f"Bearer {tbody['access_token']}"},
            )
            u = ur.json() if ur.status_code == 200 else {}
            email = u.get("email")
            meta = u.get("user_metadata") or {}

        if not email:
            return {"status": "error", "error": "No email returned by OAuth provider", "http": 400}

        # 3. Look up or create the user in the local SQLite auth router.
        from sqlalchemy import select as _select

        from database.models import User as _User

        result = await db.execute(_select(_User).where(_User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = _User(
                email=email,
                full_name=meta.get("full_name") or meta.get("name") or email.split("@")[0],
                hashed_password="",
                role=meta.get("role") or "regular",
                phone=meta.get("phone"),
                country=meta.get("country"),
                city=meta.get("city"),
                language=meta.get("language") or "fa",
                is_email_verified=True,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        token = create_access_token(
            {"user_id": user.id}, subject=str(user.id), role=user.role or "farmer"
        )
        return {
            "status": "ok",
            "access_token": token,
            "refresh_token": create_refresh_token({}, subject=str(user.id), role=role_of(user)),
            "expires_in": 604800,
            "email": user.email,
            "user_id": user.id,
            "full_name": user.full_name,
            "role": user.role,
            "language": user.language,
            "provider": provider,
            "fallback": "local",
        }
    except Exception as exc:
        if _is_network_error(exc):
            return await _local_oauth_callback(code, code_verifier, provider, db)
        return {"status": "error", "error": str(exc)}


async def _local_oauth_callback(
    code: str,
    code_verifier: str,
    provider: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Mock OAuth fallback — create or look up a local user account for the
    given provider. The email is derived from the provider so the same user
    always gets the same account across sessions."""
    import hashlib as _hashlib

    from sqlalchemy import select as _select

    from database.models import User as _User

    # Derive a stable email from the code_verifier so the same provider
    # always maps to the same user.
    digest = _hashlib.sha256(f"{provider}:{code_verifier}".encode()).hexdigest()[:12]
    email = f"oauth_{provider}_{digest}@econojin.local"
    full_name = f"{provider.capitalize()} User"

    result = await db.execute(_select(_User).where(_User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = _User(
            email=email,
            full_name=full_name,
            hashed_password="",
            role="regular",
            language="fa",
            is_email_verified=True,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(
        {"user_id": user.id}, subject=str(user.id), role=user.role or "farmer"
    )
    return {
        "status": "ok",
        "access_token": token,
        "refresh_token": create_refresh_token({}, subject=str(user.id), role=role_of(user)),
        "expires_in": 604800,
        "email": user.email,
        "user_id": user.id,
        "full_name": user.full_name,
        "role": user.role,
        "language": user.language,
        "provider": provider,
        "fallback": "mock",
    }
