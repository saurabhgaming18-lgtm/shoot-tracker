"""
Shoot Tracker & Call Sheets Manager
Handles:
- Creating and managing Shoot Tracker records & Call Sheets
- Project Names, Client & Contact Persons, Deliverables, Dates, Call Times, Locations
- Generating Standalone Printable Call Sheets (HTML/PDF)

Branding: Saurabh Patil - Production Manager
"""

from datetime import datetime
import re
from typing import List, Dict, Optional, Any

DEFAULT_STARTER_BRIEFS = []

class BriefManager:
    def __init__(self, data_store: Dict[str, Any]):
        self.data_store = data_store
        if "shoot_briefs" not in self.data_store:
            self.data_store["shoot_briefs"] = []

    def get_all_briefs(self) -> List[Dict[str, Any]]:
        briefs = self.data_store.get("shoot_briefs", [])
        for b in briefs:
            b["is_editable"] = self.is_editable(b)
        return briefs

    def find_brief_by_id(self, brief_id: str) -> Optional[Dict[str, Any]]:
        for b in self.data_store.get("shoot_briefs", []):
            if b.get("id", "").strip().upper() == brief_id.strip().upper():
                return b
        return None

    def delete_brief(self, brief_id: str) -> bool:
        briefs = self.data_store.get("shoot_briefs", [])
        for i, b in enumerate(briefs):
            if b.get("id", "").strip().upper() == brief_id.strip().upper():
                briefs.pop(i)
                return True
        return False

    def is_editable(self, brief: Dict[str, Any]) -> bool:
        created_date = brief.get("created_date")
        if not created_date:
            created_at = brief.get("created_at", "")
            if created_at:
                created_date = created_at.split()[0]
            else:
                created_date = datetime.now().strftime("%Y-%m-%d")
        
        today_date = datetime.now().strftime("%Y-%m-%d")
        return created_date == today_date

    def update_brief(self, brief_id: str, updated_data: Dict[str, Any]) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        b = self.find_brief_by_id(brief_id)
        if not b:
            return False, "Shoot record not found", None

        # Check Same-Day Edit Rule
        if not self.is_editable(b):
            created_date = b.get("created_date") or (b.get("created_at", "").split()[0] if b.get("created_at") else "previous date")
            return False, f"Edits are only accepted on the same day of entry (Created: {created_date}). Next-day editing is locked.", None

        # Apply updates
        for key, val in updated_data.items():
            if key not in ["id", "created_at", "created_date"] and val is not None:
                b[key] = val

        b["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        b["is_editable"] = self.is_editable(b)
        return True, "Shoot updated successfully", b

    def update_status(self, brief_id: str, new_status: str) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        b = self.find_brief_by_id(brief_id)
        if not b:
            return False, "Shoot record not found", None
        
        b["status"] = new_status
        b["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        b["is_editable"] = self.is_editable(b)
        return True, f"Status updated to {new_status}", b

    def create_brief(self, brief_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now()
        raw_date = brief_data.get("shoot_date") or now.strftime("%Y-%m-%d")
        
        # Extract digits for date in ID (e.g. 20260813)
        digits = re.sub(r'\D', '', str(raw_date))
        if len(digits) >= 6:
            date_code = digits[:8]
        else:
            date_code = now.strftime('%Y%m%d')

        count = len(self.data_store.get('shoot_briefs', [])) + 1
        shoot_id = brief_data.get("id") or f"SHOOT-{date_code}-{count:02d}"
        
        record = {
            "id": shoot_id,
            "project_name": brief_data.get("project_name", "New Shoot Project"),
            "client": brief_data.get("client", "Client"),
            "contact_person": brief_data.get("contact_person") or brief_data.get("client_contact", "Client POC"),
            "deliverables": brief_data.get("deliverables") or brief_data.get("concept", "Shoot Coverage & Deliverables"),
            "shoot_date": raw_date,
            "shoot_end_date": brief_data.get("shoot_end_date") or raw_date,
            "call_time": brief_data.get("call_time", "07:00 AM"),
            "location": brief_data.get("location", "Studio Location"),
            "gps_coordinates": brief_data.get("gps_coordinates", "N/A"),
            "parking_info": brief_data.get("parking_info", "On-site parking available"),
            "hospital": brief_data.get("hospital", "Nearest General Hospital"),
            "key_contacts": brief_data.get("key_contacts", "Saurabh Patil - Production Manager"),
            "concept": brief_data.get("concept", ""),
            "scenes_summary": brief_data.get("scenes_summary", ""),
            "cast_talent": brief_data.get("cast_talent", ""),
            "equipment_manifest": brief_data.get("equipment_manifest", ""),
            "catering_plan": brief_data.get("catering_plan", "Standard catering schedule"),
            "special_reqs": brief_data.get("special_reqs", "None"),
            "status": brief_data.get("status", "Active"),
            "created_at": brief_data.get("created_at") or now.strftime("%Y-%m-%d %H:%M:%S"),
            "created_date": brief_data.get("created_date") or now.strftime("%Y-%m-%d"),
            "is_editable": True
        }
        
        self.data_store.setdefault("shoot_briefs", []).insert(0, record)
        return record

    def render_call_sheet_html(self, brief_id: str) -> Optional[str]:
        b = self.find_brief_by_id(brief_id)
        if not b:
            return None

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CALL SHEET - {b.get('project_name')}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
  .callsheet {{ max-width: 880px; margin: 0 auto; background: #1e293b; border-radius: 12px; border: 1px solid #334155; padding: 32px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
  .header {{ border-bottom: 2px solid #eab308; padding-bottom: 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; }}
  .title {{ font-size: 26px; font-weight: 900; color: #eab308; margin: 0; letter-spacing: 0.05em; }}
  .subtitle {{ font-size: 14px; color: #94a3b8; margin-top: 4px; }}
  .calltime-banner {{ background: linear-gradient(135deg, #ca8a04 0%, #eab308 100%); color: #0f172a; border-radius: 8px; padding: 16px 24px; display: flex; justify-content: space-around; font-weight: 800; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }}
  .calltime-item {{ text-align: center; }}
  .calltime-item .lbl {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.85; }}
  .calltime-item .time {{ font-size: 24px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
  .card-box {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 18px; }}
  .box-title {{ font-size: 13px; font-weight: 800; color: #eab308; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; border-bottom: 1px solid #1e293b; padding-bottom: 6px; }}
  .info-line {{ font-size: 13px; margin-bottom: 8px; line-height: 1.4; color: #e2e8f0; }}
  .info-line strong {{ color: #94a3b8; }}
  .alert-box {{ background: #450a0a; border: 1px solid #ef4444; border-radius: 8px; padding: 14px; margin-bottom: 20px; }}
  .alert-title {{ font-size: 12px; font-weight: 800; color: #f87171; text-transform: uppercase; }}
  .alert-content {{ font-size: 13px; color: #fca5a5; margin-top: 4px; }}
  .footer {{ margin-top: 24px; padding-top: 14px; border-top: 1px solid #334155; display: flex; justify-content: space-between; font-size: 12px; color: #64748b; }}
  .action-bar {{ margin-bottom: 20px; max-width: 880px; margin: 0 auto 16px auto; display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }}
  .btn {{ background: #eab308; color: #0f172a; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 13px; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }}
  .btn:hover {{ background: #ca8a04; }}
  .btn-wa {{ background: #22c55e; color: #ffffff; }}
  .btn-wa:hover {{ background: #16a34a; }}
  @media print {{
    .action-bar {{ display: none; }}
    body {{ background: white; color: black; padding: 0; }}
    .callsheet {{ background: white; border: none; box-shadow: none; padding: 0; }}
    .card-box {{ background: #f8fafc; border: 1px solid #e2e8f0; }}
    .box-title {{ color: #b45309; border-color: #e2e8f0; }}
    .info-line {{ color: #0f172a; }}
    .info-line strong {{ color: #475569; }}
    .calltime-banner {{ background: #fef08a; color: #713f12; }}
    .alert-box {{ background: #fee2e2; border-color: #f87171; }}
    .alert-title {{ color: #b91c1c; }}
    .alert-content {{ color: #7f1d1d; }}
  }}
</style>
<script>
function shareWhatsApp() {{
  const text = `🎬 *PRODUCTION CALL SHEET & SHOOT BRIEF*\\n━━━━━━━━━━━━━━━━━━━━\\n🎯 *Project:* {b.get('project_name')}\\n🏢 *Client:* {b.get('client')}\\n👤 *Client POC:* {b.get('contact_person', b.get('client'))}\\n📦 *Deliverables:* {b.get('deliverables') or 'Shoot Coverage'}\\n📅 *Shoot Date:* {b.get('shoot_date')}\\n⏰ *Call Time:* {b.get('call_time')}\\n📍 *Location:* {b.get('location')}\\n👥 *Crew / Team:* {b.get('cast_talent') or b.get('key_contacts')}\\n🎥 *Equipment for Shoot:* {b.get('equipment_manifest') or b.get('equipment_for_shoot') or 'Cameras & Gear Kit'}\\n━━━━━━━━━━━━━━━━━━━━\\n📋 *Production Manager:* Saurabh Patil\\n⚠️ *Please report on time. Have a safe shoot!*`;
  window.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(text), '_blank');
}}
function copyWhatsAppText() {{
  const text = `🎬 *PRODUCTION CALL SHEET & SHOOT BRIEF*\\n━━━━━━━━━━━━━━━━━━━━\\n🎯 *Project:* {b.get('project_name')}\\n🏢 *Client:* {b.get('client')}\\n👤 *Client POC:* {b.get('contact_person', b.get('client'))}\\n📦 *Deliverables:* {b.get('deliverables') or 'Shoot Coverage'}\\n📅 *Shoot Date:* {b.get('shoot_date')}\\n⏰ *Call Time:* {b.get('call_time')}\\n📍 *Location:* {b.get('location')}\\n👥 *Crew / Team:* {b.get('cast_talent') or b.get('key_contacts')}\\n🎥 *Equipment for Shoot:* {b.get('equipment_manifest') or b.get('equipment_for_shoot') or 'Cameras & Gear Kit'}\\n━━━━━━━━━━━━━━━━━━━━\\n📋 *Production Manager:* Saurabh Patil\\n⚠️ *Please report on time. Have a safe shoot!*`;
  navigator.clipboard.writeText(text).then(() => alert('📋 WhatsApp Shoot Note copied to clipboard! Paste directly into WhatsApp.'));
}}
</script>
</head>
<body>
<div class="action-bar">
  <button class="btn btn-wa" onclick="shareWhatsApp()">📲 Share to WhatsApp</button>
  <button class="btn" style="background: #0284c7; color: white;" onclick="copyWhatsAppText()">📋 Copy WhatsApp Note</button>
  <a class="btn" style="background: #0ea5e9; color: #ffffff;" href="/api/brief/checklist/{b.get('id')}" target="_blank">📋 Camera Crew Equipment Checklist</a>
  <button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
  <a class="btn" style="background: #334155; color: white;" href="/api/brief/download/{b.get('id')}">📥 Download Call Sheet</a>
</div>

<div class="callsheet">
  <div class="header">
    <div style="display: flex; align-items: center; gap: 16px;">
      <img src="/static/logo_white.png" alt="Lightpaper Creations" style="height: 48px; width: auto; object-fit: contain;">
      <div>
        <h1 class="title">LIGHTPAPER CREATIONS • CALL SHEET</h1>
        <div class="subtitle">PROJECT: <strong>{b.get('project_name')}</strong> | CLIENT: {b.get('client')}</div>
      </div>
    </div>
    <div style="text-align: right; font-size: 13px; color: #94a3b8;">
      DATE: <strong style="color: #f8fafc;">{b.get('shoot_date')}</strong><br>
      REF: {b.get('id')}
    </div>
  </div>

  <div class="calltime-banner">
    <div class="calltime-item" style="width: 100%;">
      <div class="lbl">CREW CALL / REACH TIME</div>
      <div class="time">{b.get('call_time')}</div>
    </div>
  </div>

  <div class="grid-2">
    <div class="card-box">
      <div class="box-title">📍 LOCATION & DELIVERABLES</div>
      <div class="info-line"><strong>Location:</strong> {b.get('location')}</div>
      <div class="info-line"><strong>Deliverables:</strong> <span style="color: #38bdf8;">{b.get('deliverables') or 'Shoot Coverage'}</span></div>
      <div class="info-line"><strong>Client POC:</strong> {b.get('contact_person', b.get('client'))}</div>
    </div>

    <div class="card-box">
      <div class="box-title">👥 ASSIGNED CREW & CONTACTS</div>
      <div class="info-line"><strong>Assigned Team:</strong> {b.get('cast_talent') or b.get('key_contacts')}</div>
      <div class="info-line"><strong>Production Manager:</strong> Saurabh Patil</div>
      <div class="info-line"><strong>Status:</strong> {b.get('status', 'Active')}</div>
    </div>
  </div>

  <div class="card-box" style="margin-bottom: 20px;">
    <div class="box-title">📦 EQUIPMENT FOR SHOOT</div>
    <div class="info-line" style="font-size: 14px; color: #38bdf8; font-weight: 600;">{b.get('equipment_manifest') or b.get('equipment_for_shoot') or 'Cameras, Lenses, Lighting & Production Gear Kit'}</div>
  </div>

  <div class="footer">
    <div>Please arrive on time. Report immediately to the Production Desk (Saurabh Patil).</div>
    <div>Generated via Saurabh Patil - Production Manager</div>
  </div>
</div>
</body>
</html>
"""

    def render_equipment_checklist_html(self, brief_id: str) -> Optional[str]:
        """
        Generates a printable 2-Stage Camera Crew Equipment Checklist:
        - STAGE 1: Pre-Shoot Departure Verification (Studio Packing)
        - STAGE 2: Post-Shoot Wrap & Return Verification (Location Collection)
        """
        b = self.find_brief_by_id(brief_id)
        if not b:
            return None

        # Extract & parse equipment items
        raw_equip = b.get('equipment_manifest') or b.get('equipment_for_shoot') or ''
        raw_items = [x.strip() for x in re.split(r'[,;\n\+]+', raw_equip) if x.strip()]
        
        # Pull inventory database to cross-reference
        inventory = self.data_store.get('inventory', [])
        
        equip_rows = []
        for idx, item_str in enumerate(raw_items, 1):
            # Try to match inventory item
            match_inv = None
            for inv in inventory:
                if inv.get('name', '').lower() in item_str.lower() or inv.get('model', '').lower() in item_str.lower() or inv.get('id', '').lower() in item_str.lower():
                    match_inv = inv
                    break
            
            category = match_inv.get('category', 'Equipment') if match_inv else 'Camera Kit'
            asset_id = match_inv.get('id', f'EQ-{idx:02d}') if match_inv else f'EQ-{idx:02d}'
            
            equip_rows.append({
                "num": idx,
                "name": item_str,
                "category": category,
                "asset_id": asset_id
            })

        # If empty, add standard placeholders
        if not equip_rows:
            equip_rows = [
                {"num": 1, "name": "Primary Camera Body + Sensor Cap", "category": "Camera", "asset_id": "CAM-01"},
                {"num": 2, "name": "Primary Lens + Lens Hood & Caps", "category": "Lens", "asset_id": "LEN-01"},
                {"num": 3, "name": "Speedlight / Flash Unit + Triggers", "category": "Lighting", "asset_id": "LGT-01"},
                {"num": 4, "name": "Camera Batteries (Fully Charged x4)", "category": "Power", "asset_id": "PWR-01"},
                {"num": 5, "name": "High-Speed Memory Cards (Formatted x2)", "category": "Media", "asset_id": "MED-01"},
                {"num": 6, "name": "Heavy-Duty Tripod / Monopod", "category": "Grip", "asset_id": "GRP-01"}
            ]

        # Generate HTML rows
        table_rows_html = ""
        for r in equip_rows:
            table_rows_html += f"""
            <tr>
              <td class="col-num">{r['num']}</td>
              <td class="col-item">
                <div class="item-title">{r['name']}</div>
              </td>
              <td class="col-cat"><span class="cat-pill">{r['category']}</span> <span class="asset-tag">{r['asset_id']}</span></td>
              <td class="col-check">
                <div class="check-box-wrapper">
                  <span class="print-checkbox"></span>
                  <span class="check-lbl">Packed & Tested</span>
                </div>
                <div class="note-line">Bat/Status: ________________</div>
              </td>
              <td class="col-check">
                <div class="check-box-wrapper">
                  <span class="print-checkbox"></span>
                  <span class="check-lbl">Packed & Returned</span>
                </div>
                <div class="note-line">Condition: ________________</div>
              </td>
            </tr>
            """

        # Extra blank rows for crew add-ons
        start_blank = len(equip_rows) + 1
        for i in range(start_blank, start_blank + 3):
            table_rows_html += f"""
            <tr class="blank-row">
              <td class="col-num" style="color: #94a3b8;">{i}</td>
              <td class="col-item"><div class="blank-line"></div></td>
              <td class="col-cat"><div class="blank-line" style="width: 70px;"></div></td>
              <td class="col-check">
                <div class="check-box-wrapper">
                  <span class="print-checkbox"></span>
                  <span class="check-lbl">Packed</span>
                </div>
              </td>
              <td class="col-check">
                <div class="check-box-wrapper">
                  <span class="print-checkbox"></span>
                  <span class="check-lbl">Returned</span>
                </div>
              </td>
            </tr>
            """

        crew_names = b.get('cast_talent') or b.get('key_contacts') or 'Assigned Camera Team'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Equipment Checklist - {b.get('project_name')} ({b.get('id')})</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #070a12; color: #f8fafc; padding: 24px; }}
  
  .action-bar {{ max-width: 960px; margin: 0 auto 16px auto; display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }}
  .btn {{ background: #eab308; color: #0f172a; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 13px; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }}
  .btn:hover {{ background: #ca8a04; }}
  .btn-blue {{ background: #0284c7; color: white; }}
  .btn-blue:hover {{ background: #0369a1; }}
  
  .sheet-container {{ max-width: 960px; margin: 0 auto; background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 28px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }}
  
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #38bdf8; padding-bottom: 16px; margin-bottom: 20px; }}
  .header-left {{ display: flex; align-items: center; gap: 16px; }}
  .header-logo {{ height: 46px; width: auto; object-fit: contain; }}
  .doc-title {{ font-size: 19px; font-weight: 900; letter-spacing: 0.04em; color: #ffffff; }}
  .doc-subtitle {{ font-size: 12px; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }}
  
  .meta-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; font-size: 13px; }}
  .meta-item strong {{ color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 2px; }}
  .meta-item span {{ color: #f8fafc; font-weight: 600; }}
  
  .protocol-banner {{ background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; display: flex; gap: 14px; align-items: center; }}
  .protocol-badge {{ background: #38bdf8; color: #0f172a; font-weight: 800; font-size: 11px; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; white-space: nowrap; }}
  .protocol-desc {{ font-size: 12px; color: #cbd5e1; line-height: 1.5; }}
  
  .checklist-table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 12px; }}
  .checklist-table th {{ background: #1e293b; color: #cbd5e1; text-align: left; padding: 10px 12px; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #334155; }}
  .checklist-table td {{ padding: 10px 12px; border-bottom: 1px solid #1e293b; vertical-align: middle; }}
  .checklist-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
  
  .col-num {{ width: 35px; text-align: center; font-weight: 700; color: #64748b; }}
  .col-item {{ width: 34%; }}
  .item-title {{ font-weight: 700; color: #f8fafc; font-size: 13px; }}
  .col-cat {{ width: 18%; }}
  .cat-pill {{ background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #94a3b8; }}
  .asset-tag {{ font-family: monospace; font-size: 11px; color: #38bdf8; margin-left: 4px; }}
  
  .col-check {{ width: 24%; background: rgba(15, 23, 42, 0.4); }}
  .check-box-wrapper {{ display: flex; align-items: center; gap: 8px; }}
  .print-checkbox {{ width: 16px; height: 16px; border: 2px solid #38bdf8; border-radius: 3px; display: inline-block; flex-shrink: 0; }}
  .check-lbl {{ font-weight: 600; color: #cbd5e1; font-size: 11px; }}
  .note-line {{ font-size: 10px; color: #64748b; margin-top: 4px; font-family: monospace; }}
  
  .blank-line {{ border-bottom: 1px dashed #475569; height: 14px; width: 90%; }}
  
  .sign-section {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  .sign-box {{ background: rgba(30, 41, 59, 0.4); border: 1px solid #334155; border-radius: 8px; padding: 14px; }}
  .sign-box-title {{ font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #38bdf8; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }}
  .sign-field {{ font-size: 12px; color: #cbd5e1; margin-bottom: 8px; line-height: 1.8; }}
  
  .discrepancy-box {{ background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; font-size: 12px; color: #fca5a5; }}
  .discrepancy-title {{ font-weight: 800; text-transform: uppercase; color: #ef4444; margin-bottom: 6px; }}
  
  .footer {{ border-top: 1px solid #334155; padding-top: 12px; display: flex; justify-content: space-between; font-size: 11px; color: #64748b; }}

  /* Print Layout Styling */
  @media print {{
    .action-bar {{ display: none !important; }}
    body {{ background: white !important; color: #000000 !important; padding: 0 !important; font-size: 11pt; }}
    .sheet-container {{ max-width: 100% !important; border: none !important; box-shadow: none !important; padding: 0 !important; background: white !important; color: black !important; }}
    .header {{ border-bottom: 2px solid #000 !important; }}
    .doc-title {{ color: #000 !important; font-size: 16pt !important; }}
    .doc-subtitle {{ color: #333 !important; font-size: 9pt !important; }}
    .header-logo {{ filter: invert(1) grayscale(1) !important; }}
    .meta-grid {{ background: #f8fafc !important; border: 1px solid #ccc !important; color: #000 !important; }}
    .meta-item strong {{ color: #555 !important; }}
    .meta-item span {{ color: #000 !important; }}
    .protocol-banner {{ background: #f1f5f9 !important; border: 1px solid #cbd5e1 !important; }}
    .protocol-badge {{ background: #000 !important; color: #fff !important; }}
    .protocol-desc {{ color: #111 !important; }}
    .checklist-table th {{ background: #e2e8f0 !important; color: #000 !important; border-bottom: 1.5pt solid #000 !important; }}
    .checklist-table td {{ border-bottom: 1px solid #cbd5e1 !important; color: #000 !important; }}
    .col-num {{ color: #333 !important; }}
    .item-title {{ color: #000 !important; font-size: 10pt !important; }}
    .cat-pill {{ background: #eee !important; color: #333 !important; border: 1px solid #ccc !important; }}
    .asset-tag {{ color: #000 !important; }}
    .col-check {{ background: #fafafa !important; border-left: 1px solid #e2e8f0 !important; }}
    .print-checkbox {{ border: 1.5pt solid #000 !important; background: #fff !important; width: 14px !important; height: 14px !important; }}
    .check-lbl {{ color: #000 !important; }}
    .note-line {{ color: #444 !important; }}
    .blank-line {{ border-bottom: 1px dashed #999 !important; }}
    .sign-box {{ background: #f8fafc !important; border: 1px solid #cbd5e1 !important; }}
    .sign-box-title {{ color: #000 !important; font-weight: 800 !important; }}
    .sign-field {{ color: #000 !important; }}
    .discrepancy-box {{ background: #fff !important; border: 1.5pt solid #999 !important; color: #000 !important; }}
    .discrepancy-title {{ color: #000 !important; }}
    .footer {{ border-top: 1px solid #ccc !important; color: #555 !important; }}
  }}
</style>
</head>
<body>

<div class="action-bar">
  <button class="btn" onclick="window.print()">🖨️ Print Equipment Checklist (A4/Letter)</button>
  <a class="btn btn-blue" href="/api/brief/print/{b.get('id')}" target="_blank">📄 View Shoot Call Sheet</a>
  <a class="btn" style="background: #334155; color: white;" href="/api/brief/checklist_download/{b.get('id')}">📥 Download HTML</a>
</div>

<div class="sheet-container">
  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <img src="/static/logo_white.png" alt="Lightpaper Creations" class="header-logo">
      <div>
        <div class="doc-title">CAMERA CREW EQUIPMENT CHECKLIST</div>
        <div class="doc-subtitle">Lightpaper Creations • 2-Stage Dispatch & Return Verification</div>
      </div>
    </div>
    <div style="text-align: right; font-size: 12px; color: #94a3b8;">
      REF: <strong style="color: #f8fafc; font-family: monospace;">{b.get('id')}</strong><br>
      DATE: <strong style="color: #f8fafc;">{b.get('shoot_date')}</strong>
    </div>
  </div>

  <!-- Shoot Metadata -->
  <div class="meta-grid">
    <div class="meta-item">
      <strong>Project Name</strong>
      <span>{b.get('project_name')}</span>
    </div>
    <div class="meta-item">
      <strong>Client & Contact Person</strong>
      <span>{b.get('client')} ({b.get('contact_person', 'Client POC')})</span>
    </div>
    <div class="meta-item">
      <strong>Crew Call / Reach Time</strong>
      <span>⏰ {b.get('call_time')}</span>
    </div>
    <div class="meta-item">
      <strong>Shoot Location</strong>
      <span>📍 {b.get('location')}</span>
    </div>
    <div class="meta-item">
      <strong>Assigned Camera Crew</strong>
      <span style="color: #38bdf8;">👤 {crew_names}</span>
    </div>
    <div class="meta-item">
      <strong>Production Manager</strong>
      <span>Saurabh Patil (Lightpaper Creations)</span>
    </div>
  </div>

  <!-- Protocol Explanation -->
  <div class="protocol-banner">
    <div class="protocol-badge">2-Stage Verification</div>
    <div class="protocol-desc">
      <strong>Stage 1 (Before Leaving Studio):</strong> Crew inspects, powers on, and ticks each item packed for location.<br>
      <strong>Stage 2 (At Shoot Wrap):</strong> Crew accounts for and ticks all equipment repacked into gear cases before departing location.
    </div>
  </div>

  <!-- Two-Stage Table -->
  <table class="checklist-table">
    <thead>
      <tr>
        <th class="col-num">#</th>
        <th class="col-item">Equipment Item & Description</th>
        <th class="col-cat">Category / Tag</th>
        <th class="col-check">STAGE 1: PRE-SHOOT PACKING</th>
        <th class="col-check">STAGE 2: POST-SHOOT WRAP RETURN</th>
      </tr>
    </thead>
    <tbody>
      {table_rows_html}
    </tbody>
  </table>

  <!-- Sign-off & Verification Handover Blocks -->
  <div class="sign-section">
    <div class="sign-box">
      <div class="sign-box-title">📤 STAGE 1: STUDIO DISPATCH VERIFICATION</div>
      <div class="sign-field">
        <strong>Packed & Verified By (Crew):</strong> _____________________________
      </div>
      <div class="sign-field">
        <strong>Crew Signature:</strong> __________________ &nbsp; <strong>Time Out:</strong> _________
      </div>
      <div class="sign-field" style="margin-top: 6px; border-top: 1px dashed #475569; padding-top: 6px;">
        <strong>Dispatched By (Production Manager):</strong> Saurabh Patil
      </div>
      <div class="sign-field">
        <strong>PM Signature:</strong> _____________________________
      </div>
    </div>

    <div class="sign-box">
      <div class="sign-box-title">📥 STAGE 2: LOCATION WRAP & RETURN</div>
      <div class="sign-field">
        <strong>Repacked & Checked By (Crew):</strong> _____________________________
      </div>
      <div class="sign-field">
        <strong>Crew Signature:</strong> __________________ &nbsp; <strong>Wrap Time:</strong> _________
      </div>
      <div class="sign-field" style="margin-top: 6px; border-top: 1px dashed #475569; padding-top: 6px;">
        <strong>Received & Inspected By (PM):</strong> Saurabh Patil
      </div>
      <div class="sign-field">
        <strong>PM Signature:</strong> _____________________________
      </div>
    </div>
  </div>

  <!-- Discrepancy Box -->
  <div class="discrepancy-box">
    <div class="discrepancy-title">⚠️ Equipment Audit & Damage / Loss Declaration:</div>
    <div style="display: flex; gap: 20px; margin-bottom: 6px;">
      <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
        <span class="print-checkbox"></span>
        <span>All equipment returned 100% complete and in good working order.</span>
      </label>
      <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
        <span class="print-checkbox"></span>
        <span>Damage / Missing Gear reported below.</span>
      </label>
    </div>
    <div style="font-size: 11px;">
      <strong>Details of any missing items, damaged gear, or location issues:</strong><br>
      <div class="blank-line" style="width: 100%; margin-top: 8px;"></div>
      <div class="blank-line" style="width: 100%; margin-top: 10px;"></div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div>Lightpaper Creations • Official Production Command Sheet</div>
    <div>Hand this completed physical sheet back to Saurabh Patil upon return to Studio Vault.</div>
  </div>
</div>

</body>
</html>
"""
