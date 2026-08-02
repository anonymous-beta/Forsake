"""
Forsake REST API — FastAPI routes for the web dashboard.
Created by ANONYMOUS-BETA
"""

import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import config as cfg
from .core import Forsake
from .database import ForsakeDB

# ─── App Setup ────────────────────────────────────────────────────────────

app = FastAPI(
    title="Forsake Command & Control",
    version="2.0.0",
    description="Enterprise Phishing Engagement Platform — by ANONYMOUS-BETA",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Tighter CORS — adjust origins for your environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:8443",
        "http://localhost:8443",
        "https://127.0.0.1:8443",
        "http://127.0.0.1:8443",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

forsake = Forsake()
db = ForsakeDB()

# ─── API Models ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: int
    message: str

class DeployRequest(BaseModel):
    domain: str
    email: Optional[str] = None
    admin_password: Optional[str] = None
    clone_url: Optional[str] = None
    smtp_host: Optional[str] = None

class CloneRequest(BaseModel):
    url: str
    name: Optional[str] = None

class CampaignCreate(BaseModel):
    name: str
    template_id: int
    page_id: int
    smtp_id: int
    group_ids: List[int]
    launch_date: Optional[str] = None

# ─── Auth Dependency ──────────────────────────────────────────────────────

def get_current_user(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    user_id = db.validate_session(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user_id

# ─── Auth Routes ──────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request):
    # Check lockout first
    if db.is_locked_out(req.username):
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Account locked for {cfg.LOCKOUT_DURATION_MINUTES} minutes."
        )

    user_id = db.authenticate(req.username, req.password)
    if not user_id:
        ip = request.client.host if request.client else None
        db.record_failed_login(req.username, ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_hex(32)
    db.create_session(user_id, token, cfg.SESSION_DURATION_HOURS)
    db.log_action(user_id, "login", ip_address=request.client.host if request.client else None)

    return LoginResponse(token=token, user_id=user_id, message="Authenticated")

@app.post("/api/auth/logout")
def logout(request: Request, user_id: int = Depends(get_current_user)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    db.delete_session(token)
    db.log_action(user_id, "logout")
    return {"message": "Logged out"}

@app.get("/api/auth/verify")
def verify(user_id: int = Depends(get_current_user)):
    return {"valid": True, "user_id": user_id}

# ─── Dashboard Routes ────────────────────────────────────────────────────

@app.get("/api/dashboard/stats")
def dashboard_stats(user_id: int = Depends(get_current_user)):
    """Get aggregated dashboard statistics from GoPhish."""
    try:
        stats = forsake.gophish.get_dashboard_stats()
    except Exception as e:
        stats = {
            "error": str(e),
            "total_campaigns": 0, "total_sent": 0,
            "total_opened": 0, "total_clicked": 0,
            "total_submitted": 0, "total_reported": 0
        }

    deployment = forsake.status()
    stats["deployment"] = deployment

    try:
        campaigns = forsake.gophish.get_campaigns()
        stats["recent_campaigns"] = [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "status": c.get("status"),
                "created_date": c.get("created_date"),
                "total": len(c.get("results", [])),
                "opened": sum(1 for r in c.get("results", []) if r.get("opened_at")),
                "clicked": sum(1 for r in c.get("results", []) if r.get("clicked_at")),
                "submitted": sum(1 for r in c.get("results", []) if r.get("submitted_data")),
            }
            for c in (campaigns or [])[:10]
        ]
    except Exception:
        stats["recent_campaigns"] = []

    db.log_action(user_id, "dashboard_view")
    return stats

# ─── Campaign Routes ─────────────────────────────────────────────────────

@app.get("/api/campaigns")
def list_campaigns(user_id: int = Depends(get_current_user)):
    try:
        campaigns = forsake.gophish.get_campaigns()
        return campaigns or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns/{campaign_id}")
def get_campaign(campaign_id: int, user_id: int = Depends(get_current_user)):
    try:
        campaign = forsake.gophish.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns")
def create_campaign(campaign: CampaignCreate, user_id: int = Depends(get_current_user)):
    try:
        result = forsake.gophish.create_campaign(
            name=campaign.name,
            template_id=campaign.template_id,
            page_id=campaign.page_id,
            smtp_id=campaign.smtp_id,
            group_ids=campaign.group_ids,
            launch_date=campaign.launch_date,
        )
        if result:
            db.log_action(user_id, "campaign_created", json.dumps({"name": campaign.name}))
            return result
        raise HTTPException(status_code=500, detail="Failed to create campaign")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/campaigns/{campaign_id}")
def delete_campaign(campaign_id: int, user_id: int = Depends(get_current_user)):
    try:
        if forsake.gophish.delete_campaign(campaign_id):
            db.log_action(user_id, "campaign_deleted", str(campaign_id))
            return {"message": "Campaign deleted"}
        raise HTTPException(status_code=500, detail="Failed to delete campaign")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Deployment Routes ───────────────────────────────────────────────────

@app.post("/api/deploy")
def deploy(req: DeployRequest, user_id: int = Depends(get_current_user)):
    try:
        result = forsake.deploy(
            domain=req.domain,
            email=req.email,
            admin_password=req.admin_password,
            clone_url=req.clone_url,
            smtp_host=req.smtp_host,
        )
        db.save_deployment(req.domain, result)
        db.log_action(user_id, "deploy", json.dumps({"domain": req.domain}))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/teardown")
def teardown(remove_data: bool = False, user_id: int = Depends(get_current_user)):
    try:
        forsake.teardown(remove_data=remove_data)
        db.log_action(user_id, "teardown", json.dumps({"remove_data": remove_data}))
        return {"message": "Teardown complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
def status(user_id: int = Depends(get_current_user)):
    return forsake.status()

# ─── Landing Pages ───────────────────────────────────────────────────────

@app.get("/api/landing-pages")
def list_landing_pages(user_id: int = Depends(get_current_user)):
    return forsake.cloner.get_cloned_pages()

@app.post("/api/landing-pages/clone")
def clone_landing_page(req: CloneRequest, user_id: int = Depends(get_current_user)):
    try:
        path = forsake.cloner.clone(req.url, req.name)
        injected = forsake.cloner.inject_tracking(path)
        db.log_action(user_id, "page_cloned", json.dumps({"url": req.url, "path": path}))
        return {"path": path, "files_injected": injected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── GoPhish Resources ───────────────────────────────────────────────────

@app.get("/api/resources/templates")
def get_templates(user_id: int = Depends(get_current_user)):
    try:
        return forsake.gophish.get_templates() or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resources/pages")
def get_pages(user_id: int = Depends(get_current_user)):
    try:
        return forsake.gophish.get_pages() or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resources/smtp")
def get_smtp_profiles(user_id: int = Depends(get_current_user)):
    try:
        return forsake.gophish.get_smtp_profiles() or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resources/groups")
def get_groups(user_id: int = Depends(get_current_user)):
    try:
        return forsake.gophish.get_groups() or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Audit Log ───────────────────────────────────────────────────────────

@app.get("/api/audit-log")
def get_audit_log(limit: int = 100, user_id: int = Depends(get_current_user)):
    return db.get_audit_log(limit)

# ─── WebSocket for Real-Time Updates ─────────────────────────────────────

connected_clients = set()

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Require token via query parameter: /api/ws?token=...
    token = websocket.query_params.get("token")
    user_id = db.validate_session(token) if token else None

    if not user_id:
        await websocket.close(code=1008)  # Policy Violation
        return

    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        connected_clients.discard(websocket)

async def broadcast_update(data: dict):
    """Broadcast update to all connected WebSocket clients."""
    for client in connected_clients.copy():
        try:
            await client.send_json(data)
        except Exception:
            connected_clients.discard(client)

# ─── Serve Frontend ──────────────────────────────────────────────────────

WEB_DIR = Path(__file__).parent.parent / "web"

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/campaigns", response_class=HTMLResponse)
@app.get("/deploy", response_class=HTMLResponse)
@app.get("/landing-pages", response_class=HTMLResponse)
@app.get("/settings", response_class=HTMLResponse)
@app.get("/audit-log", response_class=HTMLResponse)
async def serve_frontend():
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return HTMLResponse("<h1>Forsake — Frontend not found</h1>")

# Serve static files
if (WEB_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(WEB_DIR / "css")), name="css")
if (WEB_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(WEB_DIR / "js")), name="js")
