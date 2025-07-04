from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Literal, Optional

# ایمپورت ابزارها و منابع داخلی پروژه
# Import internal project modules
from .utils import (
    scan_manual_domains,
    scan_manual_ips,
    get_clean_ips_with_lowest_ping,
    DomainScanner,
)
from .sources import get_active_sources

# ساخت اپلیکیشن FastAPI
# Create FastAPI application
app = FastAPI()

# روت اصلی برای بررسی آنلاین بودن سرور
# Root endpoint for server health check
@app.get("/")
async def root():
    return PlainTextResponse("Server is running", status_code=200)

# فعال‌سازی CORS برای کلاینت‌ها
# Enable CORS for client access (should be restricted in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# وضعیت هر نوع اسکن (برای پیگیری پیشرفت)
# Scan progress states for different types
progress_states = {
    "reality": {"total": 0, "done": 0, "results": [], "cancel": False, "running": False},
    "fastly": {"total": 0, "done": 0, "results": [], "cancel": False, "running": False},
    "cloudflare": {"total": 0, "done": 0, "results": [], "cancel": False, "running": False},
}


class ManualScanRequest(BaseModel):
    """
    مدل ورودی برای اسکن دستی دامنه یا IP
    Input model for manual domain or IP scan
    """
    items: List[str]
    use_tls_check: Optional[bool] = True  # فعال یا غیرفعال بودن بررسی TLS / Whether to check TLS


@app.get("/clean-items/auto/start")
async def start_auto_scan(
    background_tasks: BackgroundTasks,
    type: Literal["reality", "fastly", "cloudflare"] = "reality",
    required_count: int = Query(2, ge=1, le=100),
    use_tls_check: bool = Query(True),
):
    """
    شروع اسکن خودکار بر اساس نوع داده (Reality, Fastly, Cloudflare)
    Start auto scanning process for domains or IPs
    """
    state = progress_states[type]
    if state["running"]:
        return {"status": "already_running"}

    # ریست وضعیت اسکن
    # Reset scan state
    state.update({
        "running": True,
        "done": 0,
        "total": 0,
        "results": [],
        "cancel": False,
    })

    async def run_scan(scan_type: str, state_: dict, required_count_: int, use_tls_check_: bool):
        # تابع داخلی برای اجرای اسکن پس‌زمینه
        # Internal function to run the scan as background task
        print(f"[+] Scan started for {scan_type} with required_count={required_count_}, tls_check={use_tls_check_}")
        try:
            if scan_type == "reality":
                scanner = DomainScanner()
                sources = get_active_sources()
                domains = await scanner.fetch_all_from_sources(sources, progress=state_)
                await scanner.scan_items(domains, progress=state_)
            else:
                results = await get_clean_ips_with_lowest_ping(
                    provider=scan_type,
                    required_count=required_count_,
                    progress=state_,
                    use_tls_check=use_tls_check_,
                )
                state_["results"] = results
                state_["done"] = len(results)
                state_["total"] = int(required_count_ * 2.5)  # تخمین تعداد کل بررسی‌شده / estimated
        finally:
            state_["running"] = False
            print(f"[✓] Scan finished for {scan_type}, results: {len(state_['results'])}")

    # افزودن اسکن به تسک‌های پس‌زمینه
    # Add scan to background tasks
    background_tasks.add_task(run_scan, type, state, required_count, use_tls_check)

    return {"status": "started", "type": type, "requested": required_count}


@app.get("/clean-items/auto/progress")
async def get_progress(type: Literal["reality", "fastly", "cloudflare"] = "reality"):
    """
    دریافت وضعیت فعلی اسکن (مقدار پیشرفت، نتایج موقت و غیره)
    Get current scan progress (done, total, partial results, etc.)
    """
    state = progress_states[type]
    return {
        "total": state["total"],
        "done": state["done"],
        "results_count": len(state["results"]),
        "results": state["results"],
        "cancel": state["cancel"],
        "running": state["running"],
        "type": type,
    }


@app.post("/clean-items/auto/cancel")
async def cancel_scan(type: Literal["reality", "fastly", "cloudflare"] = "reality"):
    """
    لغو اسکن خودکار در حال اجرا
    Cancel an ongoing auto scan
    """
    state = progress_states[type]
    if not state["running"]:
        return {"status": "not_running", "type": type}
    state["cancel"] = True
    return {"status": "canceled", "type": type}


@app.post("/clean-items/manual/check")
async def manual_check(
    type: Literal["reality", "fastly", "cloudflare"] = Query("reality"),
    req: ManualScanRequest = Body(...),
):
    """
    اسکن دستی دامنه یا IP به تعداد دلخواه کاربر
    Manually scan a list of domains or IPs based on selected type
    """
    if not req.items:
        raise HTTPException(status_code=400, detail="List is empty")

    use_tls_check = req.use_tls_check if req.use_tls_check is not None else True

    if type == "reality":
        results = await scan_manual_domains(req.items)
    elif type in ("fastly", "cloudflare"):
        results = await scan_manual_ips(req.items, provider=type, use_tls_check=use_tls_check)
    else:
        raise HTTPException(status_code=400, detail=f"نوع نامعتبر: {type} / Invalid type")

    return {"type": type, "results": results}
