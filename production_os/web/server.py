"""
FastAPI Server for Production Manager OS
Provides full REST API, Web UI, Excel download, printable/downloadable DPR/Call Sheets, receipt image uploads, and AI command bridge.

Branding: Saurabh Patil - Production Manager
"""

import os
import uuid
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from production_os.core.production_engine import ProductionEngine
from production_os.core.ai_agent import ProductionAIAgent

app = FastAPI(title="Saurabh Patil - Production Manager OS")

# Initialize Master Engine & AI Agent
engine = ProductionEngine()
ai_agent = ProductionAIAgent(engine)

# Static files setup
web_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(web_dir, "static")
receipts_dir = os.path.join(engine.data_dir, "receipts")
os.makedirs(receipts_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/receipts", StaticFiles(directory=receipts_dir), name="receipts")

# ----------------------------------------------------
# Pydantic Request Models
# ----------------------------------------------------
class CheckoutRequest(BaseModel):
    project_name: str
    assigned_crew: str
    item_ids: List[str]
    expected_return: str
    condition_out: Optional[str] = "Good"
    notes: Optional[str] = ""

class CheckinRequest(BaseModel):
    dispatch_id: str
    condition_in: Optional[str] = "Good / Clean"
    damaged_notes: Optional[str] = ""

class DPRRequest(BaseModel):
    project_name: str
    date: Optional[str] = None
    day_number: Optional[str] = "Day 1"
    director: Optional[str] = "Director"
    dop: Optional[str] = "DOP"
    production_manager: Optional[str] = "Saurabh Patil"
    call_time: Optional[str] = "07:00 AM"
    first_shot_time: Optional[str] = "08:00 AM"
    lunch_time: Optional[str] = "01:00 PM - 02:00 PM"
    wrap_time: Optional[str] = "08:00 PM"
    total_hours: Optional[str] = "13 hrs"
    scenes_planned: Optional[int] = 0
    scenes_completed: Optional[int] = 0
    total_takes: Optional[int] = 0
    cards_used: Optional[int] = 0
    footage_gb: Optional[int] = 0
    crew_count: Optional[int] = 0
    cast_count: Optional[int] = 0
    breakfast: Optional[int] = 0
    lunch: Optional[int] = 0
    dinner: Optional[int] = 0
    delays_issues: Optional[str] = "None"
    weather_notes: Optional[str] = "Normal"

class BriefRequest(BaseModel):
    project_name: str
    client: Optional[str] = ""
    contact_person: Optional[str] = ""
    deliverables: Optional[str] = ""
    shoot_date: Optional[str] = None
    call_time: Optional[str] = "07:00 AM"
    location: Optional[str] = ""
    gps_coordinates: Optional[str] = ""
    parking_info: Optional[str] = ""
    hospital: Optional[str] = ""
    key_contacts: Optional[str] = "Saurabh Patil - Production Manager"
    concept: Optional[str] = ""
    scenes_summary: Optional[str] = ""
    cast_talent: Optional[str] = ""
    equipment_manifest: Optional[str] = ""
    catering_plan: Optional[str] = ""
    special_reqs: Optional[str] = ""

class ExpenseRequest(BaseModel):
    project_name: str
    date: Optional[str] = None
    category: str
    description: str
    amount: float
    paid_by: Optional[str] = "Saurabh Patil (PM)"
    mode: Optional[str] = "UPI"
    receipt_image: Optional[str] = None
    receipt_filename: Optional[str] = ""

class AddItemRequest(BaseModel):
    id: Optional[str] = None
    category: str
    name: str
    model: Optional[str] = ""
    serial: Optional[str] = "N/A"
    location: Optional[str] = "Studio Vault"
    quantity: Optional[int] = 1
    status: Optional[str] = "Available"
    notes: Optional[str] = ""

class ImportCSVRequest(BaseModel):
    csv_text: str
    append: Optional[bool] = False

class AICommandRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = "default"

# Auth Request Models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterUserRequest(BaseModel):
    username: str
    password: str
    name: str
    role: str
    phone: Optional[str] = ""
    is_admin: Optional[bool] = False

# Tracker Request Models
class MilestoneRequest(BaseModel):
    shoot_id: str
    milestone_type: str
    crew_name: Optional[str] = ""
    notes: Optional[str] = ""

class ShotRequest(BaseModel):
    shoot_id: str
    scene: str
    shot: str
    take: int = 1
    is_circle: Optional[bool] = False
    status: Optional[str] = "Good"
    notes: Optional[str] = ""
    crew_name: Optional[str] = ""
    camera_roll: Optional[str] = "A001"
    sound_roll: Optional[str] = "S001"

class EquipmentCheckRequest(BaseModel):
    item_key: str
    packed: Optional[bool] = None
    on_set: Optional[bool] = None
    returned: Optional[bool] = None
    damaged: Optional[bool] = None
    damage_notes: Optional[str] = ""
    name: Optional[str] = ""
    crew_name: Optional[str] = ""

class QuickDPRRequest(BaseModel):
    shoot_id: str
    footage_gb: Optional[int] = 0
    cards_used: Optional[int] = 0
    scenes_completed: Optional[int] = 0
    total_takes: Optional[int] = 0
    crew_count: Optional[int] = 0
    cast_count: Optional[int] = 0
    breakfast: Optional[int] = 0
    lunch: Optional[int] = 0
    dinner: Optional[int] = 0
    delays_issues: Optional[str] = "None"
    weather_notes: Optional[str] = "Normal"
    crew_name: Optional[str] = ""

# ----------------------------------------------------
# Main Web App UI Root & Mobile App Routes
# ----------------------------------------------------
@app.get("/", response_class=HTMLResponse)
@app.get("/mobile", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
async def serve_mobile_shoot_tracker():
    """Serves the Mobile Shoot Tracker app as the primary interface."""
    mobile_file = os.path.join(static_dir, "mobile.html")
    if os.path.exists(mobile_file):
        with open(mobile_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    index_file = os.path.join(static_dir, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/desktop", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def serve_desktop_dashboard():
    """Serves the desktop Production Manager command dashboard."""
    index_file = os.path.join(static_dir, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/sw.js")
async def serve_sw():
    sw_file = os.path.join(static_dir, "sw.js")
    if os.path.exists(sw_file):
        return FileResponse(sw_file, media_type="application/javascript", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    raise HTTPException(status_code=404, detail="Service worker not found")

@app.get("/manifest.json")
async def serve_manifest():
    mf_file = os.path.join(static_dir, "manifest.json")
    if os.path.exists(mf_file):
        return FileResponse(mf_file, media_type="application/json")
    raise HTTPException(status_code=404, detail="Manifest not found")


# ----------------------------------------------------
# Master Excel Sheet Download
# ----------------------------------------------------
@app.get("/api/download_excel")
async def download_master_excel():
    engine.save()
    if os.path.exists(engine.excel_path):
        return FileResponse(
            engine.excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="Production_Master_Tracker_2026.xlsx"
        )
    raise HTTPException(status_code=404, detail="Master spreadsheet not found.")

# ----------------------------------------------------
# Dashboard & Clear Data API
# ----------------------------------------------------
@app.get("/api/dashboard")
async def get_dashboard():
    return engine.get_dashboard_summary()

@app.post("/api/clear_all")
async def clear_all_data():
    engine.clear_all_data()
    return {"status": "success", "message": "All data cleared successfully."}

# ----------------------------------------------------
# Inventory Endpoints
# ----------------------------------------------------
@app.get("/api/inventory")
async def get_inventory(category: Optional[str] = None):
    return engine.equipment.get_inventory(category=category)

@app.post("/api/inventory")
async def add_item(req: AddItemRequest):
    item = engine.equipment.add_or_update_item(req.model_dump())
    engine.save()
    return item

@app.delete("/api/inventory/{item_id}")
async def delete_item(item_id: str):
    success = engine.equipment.delete_item(item_id)
    if success:
        engine.save()
        return {"status": "success", "deleted": item_id}
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/api/inventory/import")
async def import_inventory_csv(req: ImportCSVRequest):
    count = engine.equipment.import_from_csv_text(req.csv_text, append=req.append)
    engine.save()
    return {"status": "success", "count": count}

# ----------------------------------------------------
# Equipment In/Out Dispatch Endpoints
# ----------------------------------------------------
@app.get("/api/dispatches")
async def get_dispatches():
    return engine.equipment.get_logs()

@app.post("/api/checkout")
async def checkout_equipment(req: CheckoutRequest):
    log = engine.equipment.checkout_equipment(
        project_name=req.project_name,
        assigned_crew=req.assigned_crew,
        item_ids=req.item_ids,
        expected_return=req.expected_return,
        condition_out=req.condition_out,
        notes=req.notes
    )
    engine.save()
    return log

@app.post("/api/checkin")
async def checkin_equipment(req: CheckinRequest):
    res = engine.equipment.checkin_equipment(
        dispatch_id=req.dispatch_id,
        condition_in=req.condition_in,
        damaged_or_missing_notes=req.damaged_notes
    )
    if not res:
        raise HTTPException(status_code=404, detail="Dispatch record not found")
    engine.save()
    return res

@app.delete("/api/dispatches/{disp_id}")
@app.post("/api/dispatches/delete/{disp_id}")
async def delete_dispatch(disp_id: str):
    success = engine.equipment.delete_dispatch_log(disp_id)
    if success:
        engine.save()
        return {"status": "success", "deleted": disp_id}
    raise HTTPException(status_code=404, detail="Dispatch log record not found")

# ----------------------------------------------------
# DPR (Daily Production Report) Endpoints
# ----------------------------------------------------
@app.get("/api/dpr")
async def get_dprs():
    return engine.dpr.get_all_dprs()

@app.post("/api/dpr")
async def create_dpr(req: DPRRequest):
    dpr = engine.dpr.create_dpr(req.model_dump())
    engine.save()
    return dpr

@app.get("/api/dpr/print/{dpr_id}", response_class=HTMLResponse)
async def print_dpr(dpr_id: str):
    html = engine.dpr.render_dpr_html(dpr_id)
    if not html:
        raise HTTPException(status_code=404, detail="DPR not found")
    return HTMLResponse(content=html)

@app.get("/api/dpr/download/{dpr_id}")
async def download_dpr(dpr_id: str):
    html = engine.dpr.render_dpr_html(dpr_id)
    if not html:
        raise HTTPException(status_code=404, detail="DPR not found")
    dpr = engine.dpr.find_dpr_by_id(dpr_id)
    filename = f"DPR_{dpr.get('project_name','Shoot').replace(' ','_')}_{dpr.get('date')}.html"
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# ----------------------------------------------------
# Shoot Briefs & Call Sheets Endpoints
# ----------------------------------------------------
@app.get("/api/briefs")
async def get_briefs():
    return engine.briefs.get_all_briefs()

@app.post("/api/briefs")
async def create_brief(req: BriefRequest):
    b = engine.briefs.create_brief(req.model_dump())
    engine.save()
    return b

@app.get("/api/brief/print/{brief_id}", response_class=HTMLResponse)
async def print_brief(brief_id: str):
    html = engine.briefs.render_call_sheet_html(brief_id)
    if not html:
        raise HTTPException(status_code=404, detail="Shoot brief not found")
    return HTMLResponse(content=html)

@app.get("/api/brief/download/{brief_id}")
async def download_brief(brief_id: str):
    html = engine.briefs.render_call_sheet_html(brief_id)
    if not html:
        raise HTTPException(status_code=404, detail="Shoot brief not found")
    brief = engine.briefs.find_brief_by_id(brief_id)
    filename = f"CallSheet_{brief.get('project_name','Shoot').replace(' ','_')}_{brief.get('shoot_date')}.html"
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/brief/checklist/{brief_id}", response_class=HTMLResponse)
async def print_equipment_checklist(brief_id: str):
    html = engine.briefs.render_equipment_checklist_html(brief_id)
    if not html:
        raise HTTPException(status_code=404, detail="Shoot brief not found")
    return HTMLResponse(content=html)

@app.get("/api/brief/checklist_download/{brief_id}")
async def download_equipment_checklist(brief_id: str):
    html = engine.briefs.render_equipment_checklist_html(brief_id)
    if not html:
        raise HTTPException(status_code=404, detail="Shoot brief not found")
    brief = engine.briefs.find_brief_by_id(brief_id)
    filename = f"EquipmentChecklist_{brief.get('project_name','Shoot').replace(' ','_')}_{brief.get('shoot_date')}.html"
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.delete("/api/briefs/{brief_id}")
@app.post("/api/briefs/delete/{brief_id}")
async def delete_brief(brief_id: str):
    success = engine.briefs.delete_brief(brief_id)
    if success:
        engine.save()
        return {"status": "success", "deleted": brief_id}
    raise HTTPException(status_code=404, detail="Shoot record not found")

@app.put("/api/briefs/{brief_id}")
@app.post("/api/briefs/update/{brief_id}")
async def update_brief(brief_id: str, req: Dict[str, Any]):
    success, msg, record = engine.briefs.update_brief(brief_id, req)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    engine.save()
    return {"status": "success", "message": msg, "data": record}

@app.post("/api/briefs/{brief_id}/status")
@app.put("/api/briefs/{brief_id}/status")
@app.patch("/api/briefs/{brief_id}/status")
@app.post("/api/briefs/status/{brief_id}")
async def update_brief_status(brief_id: str, req: Dict[str, Any]):
    new_status = req.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Missing status parameter")
    success, msg, record = engine.briefs.update_status(brief_id, new_status)
    if not success:
        raise HTTPException(status_code=404, detail=msg)
    engine.save()
    return {"status": "success", "message": msg, "data": record}

# ----------------------------------------------------
# Expenses & Receipt Image Uploads
# ----------------------------------------------------
@app.get("/api/expenses")
async def get_expenses():
    return engine.expenses.get_all_expenses()

@app.post("/api/expenses")
async def log_expense(req: ExpenseRequest):
    exp = engine.expenses.log_expense(req.model_dump())
    engine.save()
    return exp

@app.delete("/api/expenses/{exp_id}")
async def delete_expense(exp_id: str):
    success = engine.expenses.delete_expense(exp_id)
    if success:
        engine.save()
        return {"status": "success", "deleted": exp_id}
    raise HTTPException(status_code=404, detail="Expense not found")

@app.post("/api/expenses/upload_receipt")
async def upload_receipt(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"receipt_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(receipts_dir, unique_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return {
        "status": "success",
        "url": f"/receipts/{unique_filename}",
        "filename": unique_filename
    }

# ----------------------------------------------------
# Mobile App & Manifest Routes
# ----------------------------------------------------
@app.get("/mobile", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
@app.get("/tracker", response_class=HTMLResponse)
async def serve_mobile():
    mobile_file = os.path.join(static_dir, "mobile.html")
    if os.path.exists(mobile_file):
        with open(mobile_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Mobile App Loading...</h1>")

@app.get("/manifest.json")
async def serve_manifest():
    manifest_file = os.path.join(static_dir, "manifest.json")
    if os.path.exists(manifest_file):
        return FileResponse(manifest_file, media_type="application/manifest+json")
    return Response(content="{}", media_type="application/json")

@app.get("/sw.js")
async def serve_service_worker():
    sw_file = os.path.join(static_dir, "sw.js")
    if os.path.exists(sw_file):
        return FileResponse(sw_file, media_type="application/javascript", headers={
            "Service-Worker-Allowed": "/"
        })
    return Response(content="// no-op", media_type="application/javascript")

def get_local_network_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.get("/api/network_info")
async def get_network_info(request: Request):
    ip = get_local_network_ip()
    port = request.url.port or 8000
    mobile_url = f"http://{ip}:{port}/mobile"
    return {
        "local_ip": ip,
        "port": port,
        "mobile_url": mobile_url,
        "localhost_url": f"http://localhost:{port}/mobile"
    }

# ----------------------------------------------------
# Authentication Endpoints
# ----------------------------------------------------
@app.post("/api/auth/login")
async def auth_login(req: LoginRequest):
    session = engine.users.authenticate(req.username, req.password)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    engine.save()
    return {"status": "success", "session": session}

@app.post("/api/auth/logout")
async def auth_logout(token: Optional[str] = None, request: Request = None):
    auth_header = request.headers.get("Authorization", "") if request else ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    if token:
        engine.users.logout(token)
        engine.save()
    return {"status": "success"}

@app.get("/api/auth/me")
async def auth_me(token: Optional[str] = None, request: Request = None):
    auth_header = request.headers.get("Authorization", "") if request else ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    session = engine.users.validate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return {"status": "success", "user": session}

@app.get("/api/auth/users")
async def get_all_users():
    return engine.users.list_users()

@app.post("/api/auth/register")
async def register_user(req: RegisterUserRequest):
    try:
        user = engine.users.register_user(req.model_dump())
        engine.save()
        return {"status": "success", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------------------------------------------
# Live Shoot Tracker Endpoints
# ----------------------------------------------------
@app.get("/api/tracker/shoots")
async def get_tracker_shoots():
    return engine.briefs.get_all_briefs()

@app.get("/api/tracker/shoot/{shoot_id}")
async def get_shoot_full_tracker(shoot_id: str):
    brief = engine.briefs.find_brief_by_id(shoot_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Shoot not found")
        
    milestones = engine.tracker.get_milestones(shoot_id)
    shots = engine.tracker.get_shots(shoot_id)
    gear_status = engine.tracker.get_shoot_equipment_status(shoot_id)
    expenses = [e for e in engine.expenses.get_all_expenses() if e.get("project_name") == brief.get("project_name") or e.get("shoot_id") == shoot_id]
    dprs = [d for d in engine.dpr.get_all_dprs() if d.get("project_name") == brief.get("project_name")]
    activity = engine.tracker.get_activity_feed(shoot_id=shoot_id, limit=30)
    
    return {
        "brief": brief,
        "milestones": milestones,
        "shots": shots,
        "gear_checklist": gear_status,
        "expenses": expenses,
        "dprs": dprs,
        "activity": activity
    }

@app.post("/api/tracker/milestones")
async def log_tracker_milestone(req: MilestoneRequest):
    m = engine.tracker.log_milestone(
        shoot_id=req.shoot_id,
        milestone_type=req.milestone_type,
        crew_name=req.crew_name or "Crew",
        notes=req.notes or ""
    )
    engine.save()
    return {"status": "success", "milestone": m}

@app.post("/api/tracker/shots")
async def log_tracker_shot(req: ShotRequest):
    s = engine.tracker.log_shot(req.model_dump())
    engine.save()
    return {"status": "success", "shot": s}

@app.delete("/api/tracker/shots/{shot_id}")
async def delete_tracker_shot(shot_id: str):
    success = engine.tracker.delete_shot(shot_id)
    if success:
        engine.save()
        return {"status": "success", "deleted": shot_id}
    raise HTTPException(status_code=404, detail="Shot not found")

@app.post("/api/tracker/shots/{shot_id}/circle")
async def toggle_circle_take(shot_id: str):
    updated = engine.tracker.toggle_circle_take(shot_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Shot not found")
    engine.save()
    return {"status": "success", "shot": updated}

@app.get("/api/tracker/equipment/{shoot_id}")
async def get_shoot_gear_checklist(shoot_id: str):
    return engine.tracker.get_shoot_equipment_status(shoot_id)

@app.post("/api/tracker/equipment/{shoot_id}")
async def update_shoot_gear_item(shoot_id: str, req: EquipmentCheckRequest):
    updated = engine.tracker.update_equipment_item(
        shoot_id=shoot_id,
        item_key=req.item_key,
        data=req.model_dump(exclude_unset=True),
        crew_name=req.crew_name or "Crew"
    )
    engine.save()
    return {"status": "success", "item": updated}

@app.get("/api/tracker/activity")
async def get_live_activity_feed(shoot_id: Optional[str] = None):
    return engine.tracker.get_activity_feed(shoot_id=shoot_id)

@app.post("/api/tracker/quick_dpr")
async def submit_quick_dpr(req: QuickDPRRequest):
    from datetime import datetime
    brief = engine.briefs.find_brief_by_id(req.shoot_id)
    project_name = brief.get("project_name", "Shoot") if brief else "Shoot"
    
    dpr_payload = {
        "project_name": project_name,
        "date": brief.get("shoot_date") if brief else datetime.now().strftime("%Y-%m-%d"),
        "footage_gb": req.footage_gb,
        "cards_used": req.cards_used,
        "scenes_completed": req.scenes_completed,
        "total_takes": req.total_takes,
        "crew_count": req.crew_count,
        "cast_count": req.cast_count,
        "breakfast": req.breakfast,
        "lunch": req.lunch,
        "dinner": req.dinner,
        "delays_issues": req.delays_issues,
        "weather_notes": req.weather_notes,
        "production_manager": req.crew_name or "Saurabh Patil"
    }
    dpr = engine.dpr.create_dpr(dpr_payload)
    engine.tracker.log_activity(
        shoot_id=req.shoot_id,
        crew_name=req.crew_name or "Crew",
        action="Logged Daily Production Report (DPR)",
        details=f"Footage: {req.footage_gb}GB, Cards: {req.cards_used}, Scenes: {req.scenes_completed}",
        category="dpr"
    )
    engine.save()
    return {"status": "success", "dpr": dpr}

# ----------------------------------------------------
# AI Production Assistant Bridge
# ----------------------------------------------------
@app.post("/api/ai/command")
async def process_ai_command(req: AICommandRequest):
    response = ai_agent.process_command(req.prompt, session_id=req.session_id or "default")
    return response
