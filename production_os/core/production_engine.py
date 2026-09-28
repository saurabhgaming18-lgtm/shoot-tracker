"""
Master Production Engine
Coordinates all production management services:
- Equipment In/Out Dispatch
- Inventory Asset Master
- Daily Production Reports (DPR)
- Shoot Briefs & Call Sheets
- Petty Cash & Budgets with Screenshot/Receipt Uploads
- Master Excel Synchronization

Branding: Saurabh Patil - Production Manager
"""

import os
import json
from typing import Dict, Any, Optional

from .equipment_manager import EquipmentManager
from .dpr_manager import DPRManager
from .brief_manager import BriefManager
from .expense_manager import ExpenseManager
from .user_manager import UserManager
from .tracker_manager import ShootTrackerManager
from .excel_sync import build_master_spreadsheet

class ProductionEngine:
    def __init__(self, data_dir: str = None, excel_path: str = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = data_dir or os.path.join(base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.db_file = os.path.join(self.data_dir, "production_db.json")
        self.excel_path = excel_path or os.path.join(self.data_dir, "Production_Master_Tracker_2026.xlsx")
        self.root_excel_path = os.path.join(os.path.dirname(base_dir), "Production_Master_Tracker_2026.xlsx")
        
        self.backup_file = os.path.join(self.data_dir, "production_db_backup.json")
        self.root_backup_file = os.path.join(os.path.dirname(base_dir), "production_db_backup.json")
        
        self.data_store: Dict[str, Any] = self._load_data()
        
        # Sub-managers
        self.equipment = EquipmentManager(self.data_store)
        self.dpr = DPRManager(self.data_store)
        self.briefs = BriefManager(self.data_store)
        self.expenses = ExpenseManager(self.data_store)
        self.users = UserManager(self.data_store)
        self.tracker = ShootTrackerManager(self.data_store)
        
        if "checklists" not in self.data_store:
            self.data_store["checklists"] = []
            
        self.save()

    def _load_data(self) -> Dict[str, Any]:
        """
        Loads database with multi-tier fail-safe backups so submitted user data is locked and protected.
        """
        # Tier 1: Primary Database file
        data = None
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict) and any(loaded.values()):
                        data = loaded
            except Exception as e:
                print(f"Notice: Loading db_file: {e}")

        # Tier 2: Local Backup file
        if not data and os.path.exists(self.backup_file):
            try:
                with open(self.backup_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict) and any(loaded.values()):
                        data = loaded
                        print("🛡️ Recovered data from local database backup.")
            except Exception:
                pass

        # Tier 3: Root Workspace Backup
        if not data and os.path.exists(self.root_backup_file):
            try:
                with open(self.root_backup_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict) and any(loaded.values()):
                        data = loaded
                        print("🛡️ Recovered data from root database backup.")
            except Exception:
                pass

        if not data:
            data = {
                "inventory": [],
                "in_out_logs": [],
                "dpr_records": [],
                "shoot_briefs": [],
                "expenses": [],
                "checklists": []
            }

        # Ensure all core collections exist
        for k in ["inventory", "in_out_logs", "dpr_records", "shoot_briefs", "expenses", "checklists"]:
            if k not in data:
                data[k] = []

        return data

    def save(self):
        """
        Persists data to JSON, creates dual redundant backups, and synchronizes Master Excel spreadsheet.
        """
        # 1. Save Primary JSON DB
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.data_store, f, indent=2, ensure_ascii=False)

        # 2. Save Dual Redundant Backups
        try:
            with open(self.backup_file, "w", encoding="utf-8") as f:
                json.dump(self.data_store, f, indent=2, ensure_ascii=False)
            with open(self.root_backup_file, "w", encoding="utf-8") as f:
                json.dump(self.data_store, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Notice: Writing backup: {e}")
            
        # 3. Synchronize Excel Workbooks
        try:
            build_master_spreadsheet(self.excel_path, self.data_store)
            build_master_spreadsheet(self.root_excel_path, self.data_store)
        except Exception as e:
            print(f"Warning syncing Excel: {e}")

    def clear_all_data(self):
        """Clears all records to provide a 100% clean dashboard for user."""
        self.data_store["inventory"] = []
        self.data_store["in_out_logs"] = []
        self.data_store["dpr_records"] = []
        self.data_store["shoot_briefs"] = []
        self.data_store["expenses"] = []
        self.data_store["checklists"] = []
        self.save()

    def get_dashboard_summary(self) -> Dict[str, Any]:
        eq_stats = self.equipment.get_equipment_stats()
        exp_summary = self.expenses.get_summary()
        dprs = self.dpr.get_all_dprs()
        briefs = self.briefs.get_all_briefs()
        
        return {
            "equipment": eq_stats,
            "expenses": exp_summary,
            "total_dprs": len(dprs),
            "latest_dpr": dprs[0] if dprs else None,
            "total_briefs": len(briefs),
            "latest_brief": briefs[0] if briefs else None,
            "active_dispatches": [l for l in self.data_store.get("in_out_logs", []) if l.get("status") == "Active Out"]
        }
