"""
Excel Synchronization Module for Production Manager
Generates and maintains the professional multi-tab Excel workbook:
- Equipment Inventory
- Equipment In/Out Log
- Daily Production Reports (DPR)
- Shoot Briefs & Call Sheets
- Budget & Petty Cash
- Production SOP & Checklist

Branding: Saurabh Patil - Production Manager
"""

import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Color Theme: Film Production Dark Slate & Amber Gold / Teal
HEADER_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Slate
HEADER_FONT = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
SUBHEADER_FILL = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
SUBHEADER_FONT = Font(name="Segoe UI", size=10, bold=True, color="F8FAFC")

CELL_FONT = Font(name="Segoe UI", size=10, color="0F172A")
BOLD_CELL_FONT = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
TITLE_FONT = Font(name="Segoe UI", size=15, bold=True, color="1E293B")
SUBTITLE_FONT = Font(name="Segoe UI", size=10, italic=True, color="64748B")

# Status Fills
STATUS_AVAILABLE = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Green
STATUS_IN_USE = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid") # Yellow
STATUS_MAINTENANCE = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid") # Red
STATUS_OVERDUE = PatternFill(start_color="FCA5A5", end_color="FCA5A5", fill_type="solid") # Strong Red

THIN_BORDER = Border(
    left=Side(style='thin', color="CBD5E1"),
    right=Side(style='thin', color="CBD5E1"),
    top=Side(style='thin', color="CBD5E1"),
    bottom=Side(style='thin', color="CBD5E1")
)

def style_header_row(ws, row_idx, headers):
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER
    ws.row_dimensions[row_idx].height = 28

def style_data_row(ws, row_idx, values, is_bold=False, alignments=None):
    for col_idx, val in enumerate(values, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=val)
        cell.font = BOLD_CELL_FONT if is_bold else CELL_FONT
        align = alignments.get(col_idx, "left") if alignments else "left"
        cell.alignment = Alignment(horizontal=align, vertical="center")
        cell.border = THIN_BORDER
        
        str_val = str(val).strip().lower() if val is not None else ""
        if str_val in ["available", "returned clean", "approved", "completed", "active"]:
            cell.fill = STATUS_AVAILABLE
        elif str_val in ["in use", "active out", "pending", "in progress"]:
            cell.fill = STATUS_IN_USE
        elif str_val in ["maintenance", "damaged", "issues", "returned with issues"]:
            cell.fill = STATUS_MAINTENANCE
        elif str_val in ["overdue", "rejected", "missing"]:
            cell.fill = STATUS_OVERDUE

    ws.row_dimensions[row_idx].height = 22

def auto_fit_columns(ws, max_col=15):
    for col in ws.iter_cols(min_row=1, max_col=max_col):
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if '\n' in val_str:
                lines = val_str.split('\n')
                max_len = max(max_len, max(len(l) for l in lines))
            else:
                max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

def build_master_spreadsheet(output_path, data_store):
    """
    Builds or overwrites the entire multi-tab Master Tracker Excel sheet.
    """
    wb = Workbook()
    
    # ----------------------------------------------------
    # TAB 1: Equipment Inventory
    # ----------------------------------------------------
    ws_inv = wb.active
    ws_inv.title = "1. Gear Inventory"
    ws_inv.views.sheetView[0].showGridLines = True
    
    # Title Block
    ws_inv.merge_cells("A1:I1")
    ws_inv["A1"] = "🎬 PRODUCTION EQUIPMENT INVENTORY & ASSET REGISTRY"
    ws_inv["A1"].font = TITLE_FONT
    ws_inv["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws_inv.row_dimensions[1].height = 30
    
    ws_inv["A2"] = f"Lightpaper Creations | Saurabh Patil - Production Manager | Active Gear Tracker"
    ws_inv["A2"].font = SUBTITLE_FONT
    ws_inv.row_dimensions[2].height = 18
    
    inv_headers = [
        "Item ID", "Category", "Item Name", "Brand & Model", "Serial Number", 
        "Default Kit Location", "Total Qty", "Status", "Condition / Notes"
    ]
    style_header_row(ws_inv, 4, inv_headers)
    
    inventory = data_store.get("inventory", [])
    aligns_inv = {1: "center", 2: "center", 5: "center", 6: "center", 7: "center", 8: "center"}
    for idx, item in enumerate(inventory, 5):
        row_vals = [
            item.get("id", f"EQ-{idx-4:03d}"),
            item.get("category", "General"),
            item.get("name", ""),
            item.get("model", ""),
            item.get("serial", "N/A"),
            item.get("location", "Studio Vault"),
            item.get("quantity", 1),
            item.get("status", "Available"),
            item.get("notes", "")
        ]
        style_data_row(ws_inv, idx, row_vals, alignments=aligns_inv)
    
    auto_fit_columns(ws_inv, len(inv_headers))

    # ----------------------------------------------------
    # TAB 2: Equipment In/Out Log
    # ----------------------------------------------------
    ws_log = wb.create_sheet(title="2. Equipment In-Out")
    ws_log.views.sheetView[0].showGridLines = True
    
    ws_log.merge_cells("A1:L1")
    ws_log["A1"] = "📦 EQUIPMENT DISPATCH & RETURN LOG (IN / OUT)"
    ws_log["A1"].font = TITLE_FONT
    ws_log.row_dimensions[1].height = 30
    
    ws_log["A2"] = f"Lightpaper Creations | Saurabh Patil - Production Manager | Active Dispatch Logs"
    ws_log["A2"].font = SUBTITLE_FONT
    ws_log.row_dimensions[2].height = 18
    
    log_headers = [
        "Dispatch ID", "Date Out", "Time Out", "Project / Shoot", "Assigned Crew (DOP/PM)",
        "Equipment Dispatched", "Condition Out", "Expected Return", "Actual Return",
        "Condition In", "Status", "Notes / Damaged Alert"
    ]
    style_header_row(ws_log, 4, log_headers)
    
    in_out_logs = data_store.get("in_out_logs", [])
    aligns_log = {1: "center", 2: "center", 3: "center", 8: "center", 9: "center", 11: "center"}
    for idx, log in enumerate(in_out_logs, 5):
        row_vals = [
            log.get("id", f"DISP-{idx-4:03d}"),
            log.get("date_out", ""),
            log.get("time_out", ""),
            log.get("project_name", ""),
            log.get("assigned_crew", ""),
            log.get("items_summary", ""),
            log.get("condition_out", "Good"),
            log.get("expected_return", ""),
            log.get("actual_return", "--"),
            log.get("condition_in", "--"),
            log.get("status", "Active Out"),
            log.get("notes", "")
        ]
        style_data_row(ws_log, idx, row_vals, alignments=aligns_log)
        
    auto_fit_columns(ws_log, len(log_headers))

    # ----------------------------------------------------
    # TAB 3: Shoot Tracker
    # ----------------------------------------------------
    ws_brief = wb.create_sheet(title="3. Shoot Tracker")
    ws_brief.views.sheetView[0].showGridLines = True
    
    ws_brief.merge_cells("A1:K1")
    ws_brief["A1"] = "🎯 PRODUCTION SHOOT TRACKER & MASTER CALL SHEETS"
    ws_brief["A1"].font = TITLE_FONT
    ws_brief.row_dimensions[1].height = 30
    
    ws_brief["A2"] = f"Lightpaper Creations | Saurabh Patil - Production Manager | Active Shoot Tracker"
    ws_brief["A2"].font = SUBTITLE_FONT
    ws_brief.row_dimensions[2].height = 18
    
    brief_headers = [
        "Shoot Ref", "Project Name", "Client & Contact Person", "Deliverables",
        "Shoot Date", "Shoot End Date", "Call Time",
        "Location", "Equipment for Shoot", "Assigned Team / PM Contacts", "Status"
    ]
    style_header_row(ws_brief, 4, brief_headers)
    
    briefs = data_store.get("shoot_briefs", [])
    aligns_brief = {1: "center", 5: "center", 6: "center", 7: "center", 11: "center"}
    for idx, brief in enumerate(briefs, 5):
        client_poc = f"{brief.get('client', '')} (POC: {brief.get('contact_person', brief.get('client', ''))})" if brief.get('contact_person') else brief.get('client', '')
        row_vals = [
            brief.get("id", f"SHOOT-{idx-4:02d}"),
            brief.get("project_name", ""),
            client_poc,
            brief.get("deliverables") or brief.get("concept", "Event & Shoot Coverage"),
            brief.get("shoot_date", ""),
            brief.get("shoot_end_date") or brief.get("shoot_date", ""),
            brief.get("call_time", ""),
            brief.get("location", ""),
            brief.get("equipment_manifest") or brief.get("equipment_for_shoot") or "Standard Production Kit",
            brief.get("key_contacts", "") or brief.get("cast_talent", ""),
            brief.get("status", "Active")
        ]
        style_data_row(ws_brief, idx, row_vals, alignments=aligns_brief)
        
    auto_fit_columns(ws_brief, len(brief_headers))

    # ----------------------------------------------------
    # TAB 4: Petty Cash & Expenses
    # ----------------------------------------------------
    ws_cash = wb.create_sheet(title="4. Petty Cash")
    ws_cash.views.sheetView[0].showGridLines = True
    
    ws_cash.merge_cells("A1:J1")
    ws_cash["A1"] = "💰 PRODUCTION PETTY CASH & ON-SET EXPENSES"
    ws_cash["A1"].font = TITLE_FONT
    ws_cash.row_dimensions[1].height = 30
    
    ws_cash["A2"] = f"Lightpaper Creations | Saurabh Patil - Production Manager | On-set Expense Tracker"
    ws_cash["A2"].font = SUBTITLE_FONT
    ws_cash.row_dimensions[2].height = 18
    
    cash_headers = [
        "Expense ID", "Date", "Project Name", "Category", "Expense Description",
        "Amount (INR)", "Paid By", "Payment Mode", "Receipt Attached", "Approval Status"
    ]
    style_header_row(ws_cash, 4, cash_headers)
    
    expenses = data_store.get("expenses", [])
    aligns_cash = {1: "center", 2: "center", 4: "center", 6: "right", 7: "center", 8: "center", 9: "center", 10: "center"}
    for idx, exp in enumerate(expenses, 5):
        has_receipt = "Yes (Attached)" if exp.get("receipt_image") else "No"
        row_vals = [
            exp.get("id", f"EXP-{idx-4:03d}"),
            exp.get("date", ""),
            exp.get("project_name", ""),
            exp.get("category", "General"),
            exp.get("description", ""),
            exp.get("amount", 0.0),
            exp.get("paid_by", ""),
            exp.get("mode", "UPI"),
            has_receipt,
            exp.get("status", "Approved")
        ]
        style_data_row(ws_cash, idx, row_vals, alignments=aligns_cash)
        
    # Total row
    tot_row = len(expenses) + 5
    ws_cash.cell(row=tot_row, column=5, value="TOTAL PRODUCTION EXPENSE:").font = BOLD_CELL_FONT
    ws_cash.cell(row=tot_row, column=5).alignment = Alignment(horizontal="right")
    ws_cash.cell(row=tot_row, column=6, value=f"=SUM(F5:F{tot_row-1})" if len(expenses) > 0 else 0).font = BOLD_CELL_FONT
    ws_cash.cell(row=tot_row, column=6).border = THIN_BORDER
    ws_cash.cell(row=tot_row, column=6).fill = SUBHEADER_FILL
    ws_cash.cell(row=tot_row, column=6).font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    
    auto_fit_columns(ws_cash, len(cash_headers))

    # ----------------------------------------------------
    # TAB 5: Production Checklist
    # ----------------------------------------------------
    ws_chk = wb.create_sheet(title="5. Checklist")
    ws_chk.views.sheetView[0].showGridLines = True
    
    ws_chk.merge_cells("A1:F1")
    ws_chk["A1"] = "✅ PRODUCTION MANAGER STANDARD OPERATING CHECKLIST"
    ws_chk["A1"].font = TITLE_FONT
    ws_chk.row_dimensions[1].height = 30
    
    ws_chk["A2"] = f"Generated via Saurabh Patil - Production Manager | SOP Milestones"
    ws_chk["A2"].font = SUBTITLE_FONT
    ws_chk.row_dimensions[2].height = 18
    
    chk_headers = ["Phase", "Task #", "Task Description", "Owner", "Deadline / Timing", "Status"]
    style_header_row(ws_chk, 4, chk_headers)
    
    checklists = data_store.get("checklists", [])
    aligns_chk = {1: "center", 2: "center", 4: "center", 5: "center", 6: "center"}
    for idx, chk in enumerate(checklists, 5):
        row_vals = [
            chk.get("phase", "Pre-Production"),
            f"T-{idx-4:02d}",
            chk.get("task", ""),
            chk.get("owner", "Saurabh Patil (PM)"),
            chk.get("timing", "T-1 Day"),
            chk.get("status", "Pending")
        ]
        style_data_row(ws_chk, idx, row_vals, alignments=aligns_chk)
        
    auto_fit_columns(ws_chk, len(chk_headers))

    # ----------------------------------------------------
    # TAB 6: Live Shoot Tracking (Mobile Clapperboard Logs)
    # ----------------------------------------------------
    ws_trk = wb.create_sheet(title="6. Live Shoot Logs")
    ws_trk.views.sheetView[0].showGridLines = True

    ws_trk.merge_cells("A1:I1")
    ws_trk["A1"] = "🎬 ON-SET LIVE SHOOT & CLAPPERBOARD LOGS (MOBILE TRACKER)"
    ws_trk["A1"].font = TITLE_FONT
    ws_trk.row_dimensions[1].height = 30

    ws_trk["A2"] = f"Real-time mobile updates from on-set crew • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws_trk["A2"].font = SUBTITLE_FONT
    ws_trk.row_dimensions[2].height = 18

    trk_headers = ["Shot ID", "Shoot / Project", "Scene #", "Shot #", "Take #", "Result (Good/NG)", "Logged By", "Time / Timestamp", "Director & Camera Notes"]
    style_header_row(ws_trk, 4, trk_headers)

    shot_logs = data_store.get("shot_logs", [])
    aligns_trk = {1: "center", 3: "center", 4: "center", 5: "center", 6: "center", 7: "center", 8: "center"}
    for idx, s in enumerate(shot_logs, 5):
        # Find project name
        p_name = s.get("shoot_id", "")
        for b in data_store.get("shoot_briefs", []):
            if b.get("id") == s.get("shoot_id"):
                p_name = b.get("project_name", p_name)
                break

        res_str = "⭐ Good (Circle)" if s.get("is_circle") or s.get("status") == "Good" else f"NG ({s.get('status','NG')})"
        row_vals = [
            s.get("id", f"SHT-{idx}"),
            p_name,
            s.get("scene", "1"),
            s.get("shot", "1"),
            s.get("take", 1),
            res_str,
            s.get("crew_name", "Crew"),
            s.get("timestamp", ""),
            s.get("notes", "")
        ]
        style_data_row(ws_trk, idx, row_vals, alignments=aligns_trk)

    auto_fit_columns(ws_trk, len(trk_headers))

    # Ensure parent dir exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    wb.save(output_path)
    return output_path
