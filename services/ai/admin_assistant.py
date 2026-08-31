"""Admin AI assistant v3 — model switching, deterministic command router, layered prompts.







v3 (admin feedback):



    - /model <alias>  → live model switching (qwen3/coder/gemma/fast/vision)



    - slash commands  → executed deterministically server-side (no LLM, no cloud limits)



    - system prompt   → loaded from editable training files services/ai/prompts/admin/*.md



    - fully offline



Honest degradation: if the LLM is unreachable, the live context itself is the answer.



Every call is audited by the calling router.



"""



from __future__ import annotations







import json



import os



import re



import time



from datetime import UTC, datetime, timedelta



from pathlib import Path



from typing import Any







import httpx



from sqlalchemy.orm import Session







_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)



PROMPTS_DIR = Path(__file__).parent / "prompts" / "admin"











def _ollama_base() -> str:



    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")











def _default_model() -> str:



    return os.getenv("OLLAMA_MODEL", "qwen3:4b")











def _llm_timeout() -> float:



    try:



        return float(os.getenv("AI_LLM_TIMEOUT", "120"))



    except ValueError:



        return 120.0











# ---------------------------------------------------------------- model registry



MODEL_REGISTRY: dict[str, dict[str, str]] = {



    "qwen3": {"name": "qwen3:4b", "fa": "همه‌کاره فارسی"},



    "coder": {"name": "qwen2.5-coder:3b", "fa": "کدنویسی و ترمیم"},



    "gemma": {"name": "gemma3:4b", "fa": "نوشتار و ترجمه"},



    "fast": {"name": "llama3.2:1b", "fa": "پاسخ سریع"},



    "vision": {"name": "qwen2.5vl:7b", "fa": "بینایی (پس از نصب)"},



}







_state = {"alias": "qwen3", "model": _default_model()}











def get_active_model() -> dict[str, str]:



    return {"alias": _state["alias"], "model": _state["model"]}











def set_active_model(alias: str) -> dict[str, str]:



    alias = alias.strip().lower().lstrip("/")



    if alias not in MODEL_REGISTRY:



        raise ValueError(f"unknown model alias '{alias}' — options: {', '.join(MODEL_REGISTRY)}")



    _state["alias"] = alias



    _state["model"] = MODEL_REGISTRY[alias]["name"]



    return {"alias": alias, "model": _state["model"]}











def list_models() -> dict[str, Any]:



    return {



        "active": dict(_state),



        "models": [



            {"alias": k, "name": v["name"], "fa": v["fa"], "active": k == _state["alias"]}



            for k, v in MODEL_REGISTRY.items()



        ],



    }











# ---------------------------------------------------------------- prompts



def load_admin_prompts() -> str:



    parts = []



    if PROMPTS_DIR.exists():



        for f in sorted(PROMPTS_DIR.glob("*.md")):



            parts.append(f"### {f.stem}\n{f.read_text(encoding='utf-8-sig').strip()}")



    if not parts:



        return "تو معاون فنی هیدروما هستی. کوتاه، فنی، فارسی پاسخ بده."



    return "\n\n".join(parts)











# ---------------------------------------------------------------- live context



def _db_context(db: Session) -> dict[str, Any]:



    from database import models







    day_ago = datetime.now(UTC) - timedelta(hours=24)



    ctx: dict[str, Any] = {}



    try:



        total = db.query(models.User).count()



        active = db.query(models.User).filter(models.User.is_active == True).count()  # noqa: E712



        ctx["کاربران"] = {"کل": total, "فعال": active, "مسدود": total - active}



    except Exception as exc:



        ctx["کاربران"] = {"خطا": str(exc)[:120]}



    try:



        logins_24h = (



            db.query(models.AuditLog)



            .filter(models.AuditLog.action == "auth.login")



            .filter(models.AuditLog.created_at >= day_ago)



            .count()



        )



        audit_24h = db.query(models.AuditLog).filter(models.AuditLog.created_at >= day_ago).count()



        ctx["امنیت_۲۴ساعت"] = {"ورودها": logins_24h, "کل_حسابرسی": audit_24h}



    except Exception as exc:



        ctx["امنیت_۲۴ساعت"] = {"خطا": str(exc)[:120]}



    try:



        errors_24h = (



            db.query(models.ErrorLog).filter(models.ErrorLog.created_at >= day_ago).count()



        )



        last_err = (



            db.query(models.ErrorLog)



            .order_by(models.ErrorLog.created_at.desc().nullslast())



            .first()



        )



        ctx["خطاها_۲۴ساعت"] = {



            "تعداد": errors_24h,



            "آخرین": (last_err.message or "")[:160] if last_err else "هیچ",



        }



    except Exception as exc:



        ctx["خطاها_۲۴ساعت"] = {"خطا": str(exc)[:120]}



    try:



        ctx["مزارع_و_تحلیل‌ها"] = {



            "مزارع": db.query(models.Farm).count(),



            "تحلیل‌های_ماهواره‌ای": db.query(models.SatelliteAnalysis).count(),



        }



    except Exception as exc:



        ctx["مزارع_و_تحلیل‌ها"] = {"خطا": str(exc)[:120]}



    return ctx











def _manual_dataset_context() -> dict[str, Any]:



    try:



        from services.data_manual import manual







        st = manual.status()



        return {"موجود": st.get("exists"), "حجم_مگابایت": st.get("size_mb"), "جدول‌ها": st.get("tables", {})}



    except Exception as exc:



        return {"خطا": str(exc)[:120]}











async def _ollama_context() -> dict[str, Any]:



    base = _ollama_base()



    model = _default_model()



    try:



        async with httpx.AsyncClient(timeout=5.0) as client:



            tags = (await client.get(f"{base}/api/tags")).json().get("models", [])



        return {"در_دسترس": True, "مدل_پیش‌فرض": model, "فهرست": [m.get("name") for m in tags]}



    except Exception as exc:



        return {"در_دسترس": False, "خطا": str(exc)[:120]}











MOTORS_INFO = {



    "aquacrop": "آماده", "irrigation": "آماده", "planting": "آماده",



    "crop_advisor": "آماده", "rusle": "نیازمند لایه DEM",



    "صفحه_اجرا": "/admin/motor-runner",



}











async def collect_admin_context(db: Session) -> dict[str, Any]:



    context: dict[str, Any] = {}



    context.update(_db_context(db))



    context["هوش_مصنوعی_محلی"] = await _ollama_context()



    context["دیتابیس_دستی_اکسل"] = _manual_dataset_context()



    context["موتورهای_علمی"] = MOTORS_INFO



    context["مدل_فعلی"] = dict(_state)



    return context











# ---------------------------------------------------------------- deterministic commands



def _cmd_users(db: Session) -> dict[str, Any]:



    ctx = _db_context(db)



    u = ctx["کاربران"]



    return {"answer": f"کاربران — کل: {u['کل']} | فعال: {u['فعال']} | مسدود: {u['مسدود']}"}











def _cmd_errors(db: Session, n: int = 5) -> dict[str, Any]:



    from database import models







    rows = (



        db.query(models.ErrorLog)



        .order_by(models.ErrorLog.created_at.desc().nullslast())



        .limit(max(1, min(n, 50)))



        .all()



    )



    items = [(r.message or "")[:120] for r in rows]



    if not items:



        return {"answer": "خطایی ثبت نشده ✓"}



    return {"answer": f"آخرین {len(items)} خطا:\n" + "\n".join(f"- {m}" for m in items)}











def _cmd_security(db: Session) -> dict[str, Any]:



    ctx = _db_context(db)



    sec = ctx["امنیت_۲۴ساعت"]



    return {"answer": f"امنیت ۲۴ ساعت — ورودها: {sec['ورودها']} | کل رویدادهای حسابرسی: {sec['کل_حسابرسی']}"}











def _cmd_help() -> dict[str, Any]:



    return {



        "answer": (



            "دستورات:\n"



            "/status — سلامت پلتفرم\n"



            "/users — آمار کاربران\n"



            "/errors [N] — آخرین خطاها\n"



            "/security — امنیت ۲۴ ساعت\n"



            "/model [alias] — سوئیچ/فهرست مدل (qwen3, coder, gemma, fast, vision)\n"



            "/run aquacrop <site> [sim_start] [sim_end] [crop] — اجرای AquaCrop\n"



            "/run irrigation <site> [days] — برنامه‌ریز آبیاری\n"



            "/run planting <site> <crop> — تقویم کاشت\n"



            "/run crop_advisor <site> — مشاور محصول\n"



            "/help — همین راهنما"



        )



    }











def _cmd_model(parts: list[str]) -> dict[str, Any]:



    if len(parts) >= 2:



        try:



            st = set_active_model(parts[1])



            return {"answer": f"مدل فعال: {st['alias']} ({st['model']})"}



        except ValueError as exc:



            return {"answer": str(exc)}



    return {"answer": f"مدل فعلی: {_state['alias']} ({_state['model']}) — گزینه‌ها: {', '.join(MODEL_REGISTRY)}"}











async def _cmd_run(db: Session, parts: list[str]) -> dict[str, Any]:



    from services.data_manual import motor_feed



    from services.scientific_motors.aquacrop_real import AquaCropSimulator



    from services.scientific_motors.crop_advisor import CropAdvisorMotor



    from services.scientific_motors.irrigation_scheduler import IrrigationSchedulerMotor



    from services.scientific_motors.planting_calendar import PlantingCalendarMotor







    if len(parts) < 3:



        return {"answer": "استفاده: /run <motor> <site_id> [پارامترها] — مثال: /run aquacrop SITE103 2022-11-01 2023-06-30 wheat"}



    kind = parts[1].lower()



    site_id = parts[2]



    if kind == "aquacrop":



        from services.scientific_motors.aquacrop_real import AquaCropSimulator







        species = parts[3] if len(parts) > 3 else "W001"



        sim = AquaCropSimulator()



        config = sim.load_config(species, site_id, "rainfed")



        result = sim.simulate(config)



        return {



            "answer": (



                f"آکواکراپ {species} @ {site_id}:\n"



                f"عملکرد: {result.yield_t_ha} t/ha | زیست‌توده: {result.biomass_t_ha} t/ha\n"



                f"آب: ET {result.total_et_mm:.0f}mm | بارش {result.total_rain_mm:.0f}mm | تنش {result.water_stress_days} روز\n"



                f"اطمینان: {result.confidence}"



            ),



            "outputs": {"yield_t_ha": result.yield_t_ha},



            "provider": "command-router",



        }







    elif kind == "irrigation":



        days = int(parts[3]) if len(parts) > 3 else 120



        bundle = motor_feed.irrigation_bundle(site_id, season_days=days)



        runner = IrrigationSchedulerMotor()



    elif kind == "planting" and len(parts) > 3:



        bundle = motor_feed.planting_bundle(site_id, [parts[3]])



        runner = PlantingCalendarMotor()



    elif kind == "crop_advisor":



        bundle = motor_feed.crop_advisor_bundle(site_id)



        runner = CropAdvisorMotor()



    else:



        return {"answer": f"موتور ناشناخته: {kind}"}



    result = await runner.execute(bundle["inputs"], bundle["parameters"])



    summary = json.dumps(result.summary, ensure_ascii=False)[:800] if result.summary else ""



    return {"answer": f"موتور {kind} — {result.status.value}\n{summary}", "outputs": result.outputs}











# ---------------------------------------------------------------- LLM chat



def _strip_think(text: str) -> str:



    return _THINK_RE.sub("", text or "").strip()











async def _chat_ollama(model: str, system: str, user: str) -> str:



    payload = {



        "model": model,



        "messages": [



            {"role": "system", "content": system},



            {"role": "user", "content": user},



        ],



        "stream": False,



        "think": False,



        "options": {"temperature": 0.2},



    }



    async with httpx.AsyncClient(timeout=_llm_timeout()) as client:



        resp = await client.post(f"{_ollama_base()}/api/chat", json=payload)



        resp.raise_for_status()



        data = resp.json()



    return _strip_think((data.get("message") or {}).get("content", ""))











async def ask_admin_assistant(



    db: Session, question: str, page: str | None = None



) -> dict[str, Any]:



    """Admin assistant v3: slash commands (deterministic) + free-form (active model)."""



    q = question.strip()







    # deterministic slash commands



    if q.startswith("/"):



        parts = q[1:].split()



        cmd = parts[0].lower()



        if cmd == "model":



            return {**_cmd_model(parts), "provider": "command-router", "model": _state["model"]}



        if cmd == "status":



            ctx = await collect_admin_context(db)



            return {"answer": json.dumps(ctx, ensure_ascii=False, default=str, indent=1),



                    "provider": "command-router", "model": _state["model"], "context": ctx}



        if cmd == "users":



            return {**_cmd_users(db), "provider": "command-router"}



        if cmd == "errors":



            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5



            return {**_cmd_errors(db, n), "provider": "command-router"}



        if cmd == "security":



            return {**_cmd_security(db), "provider": "command-router"}



        if cmd == "run":



            try:



                return {**await _cmd_run(db, parts), "provider": "command-router"}



            except Exception as exc:



                return {"answer": f"خطای اجرای موتور: {str(exc)[:200]}", "provider": "command-router"}



        if cmd == "help":



            return {**_cmd_help(), "provider": "command-router"}



        return {"answer": f"دستور ناشناخته: {cmd} — /help", "provider": "command-router"}







    # free-form → active model with live context



    context = await collect_admin_context(db)



    context_json = json.dumps(context, ensure_ascii=False, default=str, indent=1)



    system = load_admin_prompts()



    user_msg = (



        f"زمینه‌ی زنده‌ی پلتفرم (JSON):\n{context_json}\n\n"



        f"صفحه‌ی فعلی ادمین: {page or 'نامشخص'}\n\n"



        f"سوال/دستور ادمین: {q}"



    )



    model = _state["model"]



    try:



        answer = await _chat_ollama(model, system, user_msg)



        if not answer.strip():



            raise RuntimeError("empty answer from model")



    except Exception as exc:



        answer = (



            "اتصال به مدل محلی برقرار نشد؛ خلاصه‌ی وضعیت پلتفرم مستقیم از پایگاه‌داده:\n"



            + "\n".join(f"- {k}: {v}" for k, v in context.items())



            + f"\n\n(خطا: {str(exc)[:160]})"



        )



        provider = "local-context-only"



    else:



        provider = f"ollama:{model}"



    return {



        "answer": answer,



        "provider": provider,



        "model": model,



        "context": context,



        "page": page,



        "generated_at": datetime.now(UTC).isoformat(),



    }











async def admin_ai_status() -> dict[str, Any]:



    """Reachability + model availability + active model (panel banner)."""



    base = _ollama_base()



    model = _default_model()



    try:



        async with httpx.AsyncClient(timeout=5.0) as client:



            tags = (await client.get(f"{base}/api/tags")).json().get("models", [])



        names = [m.get("name") for m in tags]



        return {



            "reachable": True,



            "base_url": base,



            "model": model,



            "model_available": model in names,



            "models_count": len(names),



            "active": dict(_state),



        }



    except Exception as exc:



        return {



            "reachable": False,



            "base_url": base,



            "model": model,



            "model_available": False,



            "active": dict(_state),



            "error": str(exc)[:160],



        }