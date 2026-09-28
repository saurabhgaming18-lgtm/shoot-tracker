"""
Expense & Petty Cash Manager
Handles:
- On-Set Petty Cash & Shoot Expenses
- Category breakdowns (Food/Catering, Transport/Fuel, Location, Art/Props, Rentals, Misc)
- Approval status & Receipt Image/Screenshot Attaching

Branding: Saurabh Patil - Production Manager
"""

from datetime import datetime
from typing import List, Dict, Optional, Any

DEFAULT_STARTER_EXPENSES = []

class ExpenseManager:
    def __init__(self, data_store: Dict[str, Any]):
        self.data_store = data_store
        if "expenses" not in self.data_store:
            self.data_store["expenses"] = []

    def get_all_expenses(self, project_name: Optional[str] = None) -> List[Dict[str, Any]]:
        expenses = self.data_store.get("expenses", [])
        if project_name:
            expenses = [e for e in expenses if project_name.lower() in e.get("project_name", "").lower()]
        return expenses

    def log_expense(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now()
        exp_id = expense_data.get("id") or f"EXP-{now.strftime('%Y%m%d')}-{len(self.data_store.get('expenses', [])) + 1:03d}"
        
        record = {
            "id": exp_id,
            "date": expense_data.get("date") or now.strftime("%Y-%m-%d"),
            "project_name": expense_data.get("project_name", "General Production"),
            "category": expense_data.get("category", "Miscellaneous"),
            "description": expense_data.get("description", ""),
            "amount": float(expense_data.get("amount", 0.0)),
            "paid_by": expense_data.get("paid_by", "Saurabh Patil (PM)"),
            "mode": expense_data.get("mode", "UPI"),
            "receipt_image": expense_data.get("receipt_image", None),
            "receipt_filename": expense_data.get("receipt_filename", ""),
            "status": expense_data.get("status", "Approved")
        }
        
        self.data_store.setdefault("expenses", []).insert(0, record)
        return record

    def delete_expense(self, exp_id: str) -> bool:
        exps = self.data_store.get("expenses", [])
        for i, e in enumerate(exps):
            if e.get("id", "").strip().upper() == exp_id.strip().upper():
                exps.pop(i)
                return True
        return False

    def get_summary(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        expenses = self.get_all_expenses(project_name)
        total_amount = sum(e.get("amount", 0.0) for e in expenses)
        by_category = {}
        for e in expenses:
            cat = e.get("category", "Miscellaneous")
            by_category[cat] = by_category.get(cat, 0.0) + e.get("amount", 0.0)
            
        return {
            "total_expenses": total_amount,
            "transaction_count": len(expenses),
            "by_category": by_category
        }
