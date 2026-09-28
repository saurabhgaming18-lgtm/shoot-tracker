"""
Daily Production Report (DPR) Manager
Handles:
- Logging Daily Production Reports (Wrap Reports)
- Calculating Shoot Day Metrics (Hours, Delays, Footage, Catering Headcount)
- Generating Standalone Printable & Downloadable HTML DPR Sheets

Branding: Saurabh Patil - Production Manager
"""

from datetime import datetime
from typing import List, Dict, Optional, Any

DEFAULT_STARTER_DPRS = []

class DPRManager:
    def __init__(self, data_store: Dict[str, Any]):
        self.data_store = data_store
        if "dpr_records" not in self.data_store:
            self.data_store["dpr_records"] = []

    def get_all_dprs(self, project_name: Optional[str] = None) -> List[Dict[str, Any]]:
        records = self.data_store.get("dpr_records", [])
        if project_name:
            records = [r for r in records if project_name.lower() in r.get("project_name", "").lower()]
        return records

    def find_dpr_by_id(self, dpr_id: str) -> Optional[Dict[str, Any]]:
        for r in self.data_store.get("dpr_records", []):
            if r.get("id", "").strip().upper() == dpr_id.strip().upper():
                return r
        return None

    def create_dpr(self, dpr_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now()
        date_str = dpr_data.get("date") or now.strftime("%Y-%m-%d")
        dpr_id = dpr_data.get("id") or f"DPR-{now.strftime('%Y%m%d')}-{len(self.data_store.get('dpr_records', [])) + 1:03d}"
        
        record = {
            "id": dpr_id,
            "date": date_str,
            "project_name": dpr_data.get("project_name", "Untitled Shoot"),
            "day_number": dpr_data.get("day_number", "Day 1"),
            "director": dpr_data.get("director", "Director"),
            "dop": dpr_data.get("dop", "DOP"),
            "production_manager": dpr_data.get("production_manager", "Saurabh Patil"),
            "call_time": dpr_data.get("call_time", "07:00 AM"),
            "first_shot_time": dpr_data.get("first_shot_time", "08:00 AM"),
            "lunch_time": dpr_data.get("lunch_time", "01:00 PM - 02:00 PM"),
            "wrap_time": dpr_data.get("wrap_time", "08:00 PM"),
            "total_hours": dpr_data.get("total_hours", "13 hrs"),
            "scenes_planned": int(dpr_data.get("scenes_planned", 0)),
            "scenes_completed": int(dpr_data.get("scenes_completed", 0)),
            "total_takes": int(dpr_data.get("total_takes", 0)),
            "cards_used": int(dpr_data.get("cards_used", 0)),
            "footage_gb": int(dpr_data.get("footage_gb", 0)),
            "crew_count": int(dpr_data.get("crew_count", 0)),
            "cast_count": int(dpr_data.get("cast_count", 0)),
            "breakfast": int(dpr_data.get("breakfast", 0)),
            "lunch": int(dpr_data.get("lunch", 0)),
            "dinner": int(dpr_data.get("dinner", 0)),
            "delays_issues": dpr_data.get("delays_issues", "None"),
            "weather_notes": dpr_data.get("weather_notes", "Normal conditions"),
            "status": dpr_data.get("status", "Approved")
        }
        
        self.data_store.setdefault("dpr_records", []).insert(0, record)
        return record

    def render_dpr_html(self, dpr_id: str) -> Optional[str]:
        dpr = self.find_dpr_by_id(dpr_id)
        if not dpr:
            return None

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DPR - {dpr.get('project_name')} - {dpr.get('date')}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
  .report-card {{ max-width: 850px; margin: 0 auto; background: #1e293b; border-radius: 12px; border: 1px solid #334155; padding: 32px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #38bdf8; padding-bottom: 16px; margin-bottom: 24px; }}
  .title {{ font-size: 24px; font-weight: 800; color: #38bdf8; margin: 0; }}
  .subtitle {{ font-size: 14px; color: #94a3b8; margin-top: 4px; }}
  .badge {{ background: #0284c7; color: white; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 700; text-transform: uppercase; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }}
  .stat-box {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 14px; text-align: center; }}
  .stat-val {{ font-size: 22px; font-weight: 700; color: #38bdf8; }}
  .stat-lbl {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.05em; margin-top: 4px; }}
  .section-title {{ font-size: 15px; font-weight: 700; color: #f1f5f9; border-left: 4px solid #38bdf8; padding-left: 10px; margin: 24px 0 12px 0; }}
  .detail-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
  .detail-table td {{ padding: 8px 12px; border-bottom: 1px solid #334155; font-size: 13px; }}
  .detail-table td.lbl {{ color: #94a3b8; width: 35%; font-weight: 600; }}
  .detail-table td.val {{ color: #f8fafc; }}
  .note-box {{ background: #0f172a; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-top: 8px; font-size: 13px; line-height: 1.5; color: #e2e8f0; }}
  .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #334155; display: flex; justify-content: space-between; font-size: 12px; color: #64748b; }}
  .action-bar {{ margin-bottom: 20px; max-width: 850px; margin: 0 auto 16px auto; display: flex; justify-content: flex-end; gap: 10px; }}
  .btn {{ background: #0284c7; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 13px; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }}
  .btn:hover {{ background: #0369a1; }}
  @media print {{
    .action-bar {{ display: none; }}
    body {{ background: white; color: black; padding: 0; }}
    .report-card {{ background: white; border: none; box-shadow: none; padding: 0; }}
    .stat-box {{ background: #f8fafc; border: 1px solid #e2e8f0; }}
    .stat-val {{ color: #0284c7; }}
    .stat-lbl {{ color: #475569; }}
    .section-title {{ color: #0f172a; }}
    .detail-table td {{ border-color: #e2e8f0; }}
    .detail-table td.lbl {{ color: #475569; }}
    .detail-table td.val {{ color: #0f172a; }}
    .note-box {{ background: #f8fafc; color: #1e293b; border-left-color: #d97706; }}
  }}
</style>
</head>
<body>
<div class="action-bar">
  <button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
  <a class="btn" style="background: #334155;" href="/api/dpr/download/{dpr.get('id')}">📥 Download DPR File</a>
</div>

<div class="report-card">
  <div class="header">
    <div>
      <h1 class="title">🎬 DAILY PRODUCTION REPORT (DPR)</h1>
      <div class="subtitle">{dpr.get('project_name')} | {dpr.get('day_number')} | {dpr.get('date')}</div>
    </div>
    <div class="badge">{dpr.get('status', 'APPROVED')}</div>
  </div>

  <div class="grid-4">
    <div class="stat-box">
      <div class="stat-val">{dpr.get('scenes_completed')} / {dpr.get('scenes_planned')}</div>
      <div class="stat-lbl">Scenes Completed</div>
    </div>
    <div class="stat-box">
      <div class="stat-val">{dpr.get('total_hours')}</div>
      <div class="stat-lbl">Total Shoot Duration</div>
    </div>
    <div class="stat-box">
      <div class="stat-val">{dpr.get('footage_gb')} GB</div>
      <div class="stat-lbl">Data Dump ({dpr.get('cards_used')} Cards)</div>
    </div>
    <div class="stat-box">
      <div class="stat-val">{dpr.get('crew_count', 0) + dpr.get('cast_count', 0)}</div>
      <div class="stat-lbl">Total Headcount</div>
    </div>
  </div>

  <div class="grid-2">
    <div>
      <div class="section-title">TIMELINE & SCHEDULE</div>
      <table class="detail-table">
        <tr><td class="lbl">General Call</td><td class="val">{dpr.get('call_time')}</td></tr>
        <tr><td class="lbl">First Camera Shot</td><td class="val">{dpr.get('first_shot_time')}</td></tr>
        <tr><td class="lbl">Lunch Break</td><td class="val">{dpr.get('lunch_time')}</td></tr>
        <tr><td class="lbl">Camera Wrap</td><td class="val">{dpr.get('wrap_time')}</td></tr>
        <tr><td class="lbl">Total Takes Shot</td><td class="val">{dpr.get('total_takes')} takes</td></tr>
      </table>
    </div>

    <div>
      <div class="section-title">KEY PERSONNEL & CATERING</div>
      <table class="detail-table">
        <tr><td class="lbl">Director</td><td class="val">{dpr.get('director')}</td></tr>
        <tr><td class="lbl">Director of Photography</td><td class="val">{dpr.get('dop')}</td></tr>
        <tr><td class="lbl">Production Manager</td><td class="val">{dpr.get('production_manager', 'Saurabh Patil')}</td></tr>
        <tr><td class="lbl">Cast / Crew Headcount</td><td class="val">Cast: {dpr.get('cast_count')} | Crew: {dpr.get('crew_count')}</td></tr>
        <tr><td class="lbl">Meal Counts (B/L/D)</td><td class="val">Breakfast: {dpr.get('breakfast')} | Lunch: {dpr.get('lunch')} | Dinner: {dpr.get('dinner')}</td></tr>
      </table>
    </div>
  </div>

  <div class="section-title">PRODUCTION ISSUES, DELAYS & WEATHER</div>
  <div class="note-box">
    <strong>Technical & Production Log:</strong> {dpr.get('delays_issues')}<br>
    <strong>Environment / Weather Notes:</strong> {dpr.get('weather_notes')}
  </div>

  <div class="footer">
    <div>Report ID: <strong>{dpr.get('id')}</strong></div>
    <div>Signed Off by: <strong>{dpr.get('production_manager', 'Saurabh Patil')}</strong></div>
    <div>Generated via Saurabh Patil - Production Manager</div>
  </div>
</div>
</body>
</html>
"""
