"""
Equipment Manager Module
Handles:
- Inventory Management (CRUD & Batch Import from CSV/Excel)
- Equipment Dispatch (Check-Out)
- Equipment Return (Check-In & Condition Audit)
- Overdue Tracking & Availability Verification

Branding: Saurabh Patil - Production Manager
"""

import csv
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Any

# Starts clean and empty ready for Saurabh Patil to fill
DEFAULT_STARTER_INVENTORY = []

class EquipmentManager:
    def __init__(self, data_store: Dict[str, Any]):
        self.data_store = data_store
        if "inventory" not in self.data_store:
            self.data_store["inventory"] = []
        if "in_out_logs" not in self.data_store:
            self.data_store["in_out_logs"] = []

    def get_inventory(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self.data_store.get("inventory", [])
        if category:
            items = [it for it in items if it.get("category", "").lower() == category.lower()]
        if status:
            items = [it for it in items if it.get("status", "").lower() == status.lower()]
        return items

    def find_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        for item in self.data_store.get("inventory", []):
            if item.get("id", "").strip().upper() == item_id.strip().upper():
                return item
        return None

    def add_or_update_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        item_id = item_data.get("id")
        if not item_id:
            prefix = item_data.get("category", "EQ")[:3].upper()
            count = len(self.data_store.get("inventory", [])) + 1
            item_id = f"{prefix}-{count:03d}"
            item_data["id"] = item_id

        existing = self.find_item_by_id(item_id)
        if existing:
            existing.update(item_data)
            return existing
        else:
            self.data_store["inventory"].append(item_data)
            return item_data

    def delete_item(self, item_id: str) -> bool:
        inv = self.data_store.get("inventory", [])
        for i, item in enumerate(inv):
            if item.get("id", "").strip().upper() == item_id.strip().upper():
                inv.pop(i)
                return True
        return False

    def replace_inventory(self, new_inventory: List[Dict[str, Any]]) -> int:
        self.data_store["inventory"] = new_inventory
        return len(new_inventory)

    def import_from_csv_text(self, csv_text: str, append: bool = False) -> int:
        reader = csv.DictReader(csv_text.strip().splitlines())
        imported_items = []
        for idx, row in enumerate(reader, 1):
            item = {
                "id": row.get("Item ID") or row.get("id") or f"EQ-{idx:03d}",
                "category": row.get("Category") or row.get("category") or "General",
                "name": row.get("Item Name") or row.get("name") or "Unnamed Item",
                "model": row.get("Brand & Model") or row.get("model") or "",
                "serial": row.get("Serial Number") or row.get("serial") or "N/A",
                "location": row.get("Default Kit Location") or row.get("location") or "Studio Vault",
                "quantity": int(row.get("Total Qty") or row.get("quantity") or 1),
                "status": row.get("Status") or row.get("status") or "Available",
                "notes": row.get("Condition / Notes") or row.get("notes") or ""
            }
            imported_items.append(item)
            
        if append:
            self.data_store["inventory"].extend(imported_items)
        else:
            self.data_store["inventory"] = imported_items
            
        return len(imported_items)

    def checkout_equipment(
        self,
        project_name: str,
        assigned_crew: str,
        item_ids: List[str],
        expected_return: str,
        condition_out: str = "Good",
        notes: str = ""
    ) -> Dict[str, Any]:
        now = datetime.now()
        disp_id = f"DISP-{now.strftime('%Y%m%d')}-{len(self.data_store.get('in_out_logs', [])) + 1:03d}"
        
        item_names = []
        for i_id in item_ids:
            item = self.find_item_by_id(i_id)
            if item:
                item["status"] = "In Use"
                item_names.append(f"{item.get('name')} ({item.get('id')})")
            else:
                item_names.append(i_id)

        items_summary = ", ".join(item_names) if item_names else "Equipment Package"
        
        log_entry = {
            "id": disp_id,
            "date_out": now.strftime("%Y-%m-%d"),
            "time_out": now.strftime("%H:%M"),
            "project_name": project_name,
            "assigned_crew": assigned_crew,
            "item_ids": item_ids,
            "items_summary": items_summary,
            "condition_out": condition_out,
            "expected_return": expected_return,
            "actual_return": "--",
            "condition_in": "--",
            "status": "Active Out",
            "notes": notes
        }
        
        self.data_store.setdefault("in_out_logs", []).append(log_entry)
        return log_entry

    def checkin_equipment(
        self,
        dispatch_id: str,
        condition_in: str = "Good / Clean",
        damaged_or_missing_notes: str = ""
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now()
        target_log = None
        for log in self.data_store.get("in_out_logs", []):
            if log.get("id", "").strip().upper() == dispatch_id.strip().upper():
                target_log = log
                break
                
        if not target_log:
            return None

        target_log["actual_return"] = now.strftime("%Y-%m-%d %H:%M")
        target_log["condition_in"] = condition_in
        
        is_issue = bool(damaged_or_missing_notes.strip() or "damage" in condition_in.lower() or "missing" in condition_in.lower())
        target_log["status"] = "Returned with Issues" if is_issue else "Returned Clean"
        if damaged_or_missing_notes:
            target_log["notes"] = f"{target_log.get('notes', '')} | In-Check Note: {damaged_or_missing_notes}".strip(" | ")

        for i_id in target_log.get("item_ids", []):
            item = self.find_item_by_id(i_id)
            if item:
                if is_issue:
                    item["status"] = "Maintenance"
                    item["notes"] = f"Reported issue on return ({now.strftime('%Y-%m-%d')}): {damaged_or_missing_notes}"
                else:
                    item["status"] = "Available"

        return target_log

    def delete_dispatch_log(self, dispatch_id: str) -> bool:
        """
        Deletes a dispatch log. If the dispatch is still Active Out,
        restores the associated items back to 'Available' status.
        """
        logs = self.data_store.get("in_out_logs", [])
        target_idx = None
        target_log = None
        for idx, log in enumerate(logs):
            if log.get("id", "").strip().upper() == dispatch_id.strip().upper():
                target_idx = idx
                target_log = log
                break
                
        if target_idx is None:
            return False

        # If it was still active out, release items back to Available
        if target_log.get("status") == "Active Out":
            for i_id in target_log.get("item_ids", []):
                item = self.find_item_by_id(i_id)
                if item and item.get("status") == "In Use":
                    item["status"] = "Available"

        logs.pop(target_idx)
        return True

    def get_logs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        logs = self.data_store.get("in_out_logs", [])
        if status:
            logs = [l for l in logs if l.get("status", "").lower() == status.lower()]
        return logs

    def get_equipment_stats(self) -> Dict[str, Any]:
        inv = self.data_store.get("inventory", [])
        logs = self.data_store.get("in_out_logs", [])
        
        total = len(inv)
        available = sum(1 for x in inv if x.get("status") == "Available")
        in_use = sum(1 for x in inv if x.get("status") == "In Use")
        maintenance = sum(1 for x in inv if x.get("status") == "Maintenance")
        active_dispatches = sum(1 for x in logs if x.get("status") == "Active Out")
        
        return {
            "total_items": total,
            "available_items": available,
            "in_use_items": in_use,
            "maintenance_items": maintenance,
            "active_dispatches": active_dispatches
        }
