"""
Production Manager AI Agent
Intelligent, interactive, conversational assistant for Saurabh Patil - Production Manager OS.

Guides the user step-by-step:
- Inquires what the user needs (add gear, check out/in equipment, create call sheets, log expenses, search inventory)
- Asks targeted clarifying questions for missing details
- Executes database and Excel synchronizations seamlessly
- Remembers multi-turn context
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .production_engine import ProductionEngine
from .deepseek_client import is_deepseek_configured, query_deepseek_sync, get_deepseek_model

OFFICIAL_TEAM_MEMBERS = [
    "Rohit Salunke",
    "Vedant Mankar",
    "Akash Deshmukh",
    "Samyak Chavhan",
    "Saurabh Patil",
    "Riha Das",
    "Maulisha Guha"
]


class ProductionAIAgent:
    def __init__(self, engine: ProductionEngine):
        self.engine = engine
        # Multi-turn conversation state per session
        self.session_states: Dict[str, Dict[str, Any]] = {}

    def get_state(self, session_id: str = "default") -> Dict[str, Any]:
        if session_id not in self.session_states:
            self.session_states[session_id] = {
                "active_intent": None,  # "add_gear", "checkout", "checkin", "brief", "expense"
                "slots": {},
                "history": []
            }
        return self.session_states[session_id]

    def reset_state(self, session_id: str = "default"):
        self.session_states[session_id] = {
            "active_intent": None,
            "slots": {},
            "history": []
        }

    def process_command(self, prompt: str, session_id: str = "default") -> Dict[str, Any]:
        p = prompt.strip()
        low = p.lower()
        state = self.get_state(session_id)

        # 0. User wants to cancel / reset conversation
        if low in ["cancel", "reset", "start over", "clear chat", "nevermind", "stop", "exit"]:
            self.reset_state(session_id)
            return {
                "status": "info",
                "action": "cancel",
                "message": "🔄 Conversation reset. How else can I assist you with your gear, dispatches, call sheets, or expenses?"
            }

        # 1. Clear database command
        if any(w in low for w in ["clear all data", "wipe data", "clear database", "reset data"]):
            self.engine.clear_all_data()
            self.reset_state(session_id)
            return {
                "status": "success",
                "action": "clear_data",
                "message": "🧹 **All dashboard, database, and Excel data has been cleared!** Ready for your fresh entries."
            }

        # 2. If we are currently in an active multi-turn intent, process the reply in context
        active_intent = state.get("active_intent")
        if active_intent:
            res = self._handle_active_turn(p, low, state, session_id)
            if res is not None:
                return res

        # 3. Detect new intent or general conversational prompt
        # A. Greeting / Help / Unspecified request
        if low in ["hi", "hello", "hey", "hola", "namaste", "help", "menu", "options", "what can you do", "assistant"] or \
           any(w in low for w in ["i need help", "i want to add something", "create something", "update something", "what should i do"]):
            return self._send_welcome_menu(state)

        # B. Add Gear / Equipment Inventory
        if any(w in low for w in ["add gear", "add equipment", "add item", "new gear", "new equipment", "register gear", "bought new", "add camera", "add lens", "add light", "add mic"]):
            return self._init_add_gear(p, low, state)

        # C. Equipment Status / Availability Query
        if any(w in low for w in ["available gear", "available equipment", "available cameras", "inventory status", "show gear", "show inventory", "list gear", "find gear", "search gear"]):
            return self._handle_inventory_query(low)

        # D. Equipment Check-out (Dispatch)
        if any(w in low for w in ["checkout", "check out", "dispatch", "assign gear", "give equipment", "issue gear", "send gear"]):
            return self._init_checkout(p, low, state)

        # E. Equipment Check-in (Return)
        if any(w in low for w in ["checkin", "check in", "return equipment", "return gear", "returned gear", "bring back"]):
            return self._init_checkin(p, low, state)

        # F. Create Shoot Brief / Call Sheet / Shoot Tracker
        if any(w in low for w in ["create brief", "shoot brief", "call sheet", "make brief", "new shoot", "make call sheet", "create call sheet", "add shoot", "plan shoot"]):
            return self._init_brief(p, low, state)

        # F2. Delete Shoot from Shoot Tracker
        if any(w in low for w in ["delete shoot", "remove shoot", "cancel shoot"]):
            return self._handle_delete_shoot(p, low)

        # F3. Share Shoot on WhatsApp
        if any(w in low for w in ["whatsapp", "share on whatsapp", "send to whatsapp", "whatsapp note", "whatsapp message", "share shoot", "share brief"]):
            return self._handle_whatsapp_share(p, low)

        # F4. Update / Edit Shoot (Same-Day Window)
        if any(w in low for w in ["update shoot", "edit shoot", "change shoot", "modify shoot", "update call time", "change call time", "change location", "update location", "update deliverables", "change deliverables"]):
            return self._handle_edit_shoot(p, low)

        # F5. Update Shoot Status Anytime
        if any(w in low for w in ["change status", "update status", "mark shoot", "set status", "mark as completed", "mark as wrapped", "mark as active", "mark as in progress", "mark as scheduled", "mark as postponed", "mark as cancelled"]):
            return self._handle_update_shoot_status(p, low)

        # G. Log Expense / Petty Cash
        if any(w in low for w in ["expense", "petty cash", "spent", "paid for", "add expense", "log expense", "log bill", "cost", "receipt"]):
            return self._init_expense(p, low, state)

        # H. General Status / Summary
        if any(w in low for w in ["summary", "overview", "status", "dashboard", "what's active", "whats active", "how are we doing"]):
            return self._handle_summary()

        # I. Attempt smart extraction across all actions if prompt is detailed
        smart_res = self._try_smart_match(p, low, state)
        if smart_res:
            return smart_res

        # J. DeepSeek AI Production Intelligence Assistant
        deepseek_answer = self._query_deepseek_production_assistant(p)
        if deepseek_answer:
            return {
                "status": "success",
                "action": "deepseek_intelligence",
                "message": f"🤖 **DeepSeek Production Assistant**:\n\n{deepseek_answer}"
            }

        # K. Default conversational prompt asking what section they need
        return self._send_welcome_menu(state, custom_prefix=f"I understood: *\"{p}\"*. Let me help you route this!")

    def _query_deepseek_production_assistant(self, prompt: str) -> Optional[str]:
        """Queries DeepSeek with rich studio and production context for intelligent advisory."""
        if not is_deepseek_configured():
            return None

        gear_count = len(self.engine.equipment.get_inventory()) if hasattr(self.engine, "equipment") else 0
        shoot_count = len(self.engine.briefs.get_all_briefs()) if hasattr(self.engine, "briefs") else 0
        crew_list = ", ".join(OFFICIAL_TEAM_MEMBERS)

        system_prompt = (
            "You are the intelligent Production Intelligence Assistant for Saurabh Patil - Production Manager OS. "
            "You specialize in professional filmmaking, commercial videography, broadcast shoots, equipment management, "
            "call sheet scheduling, crew logistics, and budget tracking.\n\n"
            f"Current Studio Context:\n"
            f"- Total registered gear in inventory: {gear_count} items\n"
            f"- Active/Scheduled shoots in tracker: {shoot_count} shoots\n"
            f"- Official Crew Members: {crew_list}\n\n"
            "Provide insightful, professional, concise, and actionable guidance for the production manager. "
            "Use clear bullet points and bold highlights where appropriate."
        )
        try:
            model_name = get_deepseek_model()
            answer = query_deepseek_sync(prompt=prompt, system_prompt=system_prompt, model=model_name)
            return answer.strip() if answer else None
        except Exception:
            return None

    # ----------------------------------------------------
    # Conversational Welcome & Section Routing
    # ----------------------------------------------------
    def _send_welcome_menu(self, state: Dict[str, Any], custom_prefix: Optional[str] = None) -> Dict[str, Any]:
        state["active_intent"] = None
        state["slots"] = {}

        prefix = custom_prefix or "👋 **Hello! I'm your Production Manager AI Assistant (Saurabh Patil Desk).**"
        
        msg = (
            f"{prefix}\n\n"
            f"Tell me what you'd like to do, and I will guide you through it:\n\n"
            f"• 🎥 **1. Gear Inventory** — *'Add new gear'*, *'Show available cameras'*, *'Check inventory'*\n"
            f"• 📦 **2. Equipment Dispatch** — *'Check out equipment to crew'*, *'Check in returned gear'*\n"
            f"• 🎯 **3. Shoot Call Sheets** — *'Create a new shoot call sheet / brief'*\n"
            f"• 💰 **4. Petty Cash & Expenses** — *'Add expense of ₹2,500 for lunch'*\n"
            f"• 📊 **5. Production Overview** — *'Show production overview'* or *'Summary'*\n\n"
            f"💡 *What would you like to create, update, or add right now?*"
        )
        return {"status": "info", "action": "welcome", "message": msg}

    # ----------------------------------------------------
    # Active Multi-Turn Turn Handler
    # ----------------------------------------------------
    def _handle_active_turn(self, p: str, low: str, state: Dict[str, Any], session_id: str) -> Optional[Dict[str, Any]]:
        intent = state.get("active_intent")
        slots = state.get("slots", {})

        if intent == "add_gear":
            return self._continue_add_gear(p, low, state)
        elif intent == "checkout":
            return self._continue_checkout(p, low, state)
        elif intent == "checkin":
            return self._continue_checkin(p, low, state)
        elif intent == "brief":
            return self._continue_brief(p, low, state)
        elif intent == "expense":
            return self._continue_expense(p, low, state)

        return None

    # ----------------------------------------------------
    # 1. GEAR INVENTORY (Add / Update / Search)
    # ----------------------------------------------------
    def _init_add_gear(self, p: str, low: str, state: Dict[str, Any]) -> Dict[str, Any]:
        slots = {}
        # Try extract category
        slots["category"] = self._extract_gear_category(low)
        
        # Try extract name
        name_match = re.search(r'(?:add|register|bought|new)\s+(?:gear|item|equipment)?\s*[:\-]?\s*([A-Za-z0-9\s\.\+\-\/]+?)(?=\s+(?:category|cat|in|qty|quantity|serial|loc|location)|$)', p, re.IGNORECASE)
        if name_match and len(name_match.group(1).strip()) > 2 and not any(w == name_match.group(1).strip().lower() for w in ["camera", "lens", "light", "gear", "item"]):
            slots["name"] = name_match.group(1).strip()

        # Try extract quantity
        qty_match = re.search(r'(\d+)\s*(?:units?|pcs?|qty|pieces?|count)', low)
        if qty_match:
            slots["quantity"] = int(qty_match.group(1))

        # Try extract serial
        serial_match = re.search(r'(?:serial|sn|s\/n|sr)\s*[:\-]?\s*([A-Za-z0-9\-]+)', p, re.IGNORECASE)
        if serial_match:
            slots["serial"] = serial_match.group(1).strip()

        state["active_intent"] = "add_gear"
        state["slots"] = slots

        return self._continue_add_gear(p, low, state, is_init=True)

    def _continue_add_gear(self, p: str, low: str, state: Dict[str, Any], is_init: bool = False) -> Dict[str, Any]:
        slots = state.get("slots", {})

        if not is_init:
            # Parse user answer to fill remaining slots
            if "name" not in slots:
                slots["name"] = p.split(",")[0].strip()
            if "category" not in slots or slots["category"] == "Other":
                cat = self._extract_gear_category(low)
                if cat != "Other":
                    slots["category"] = cat
            if "quantity" not in slots:
                qty_m = re.search(r'(\d+)', low)
                if qty_m:
                    slots["quantity"] = int(qty_m.group(1))
            if "location" not in slots:
                loc_m = re.search(r'(?:in|at|loc|vault|studio|storage|bag|rack)\s*[:\-]?\s*([A-Za-z0-9\s]+)', p, re.IGNORECASE)
                if loc_m:
                    slots["location"] = loc_m.group(1).strip()
            if "serial" not in slots:
                sr_m = re.search(r'(?:serial|sn|s\/n)\s*[:\-]?\s*([A-Za-z0-9\-]+)', p, re.IGNORECASE)
                if sr_m:
                    slots["serial"] = sr_m.group(1).strip()

        # Check what is missing
        if "name" not in slots or not slots["name"]:
            return {
                "status": "inquiry",
                "action": "ask_gear_name",
                "message": (
                    "🎥 **Let's add this equipment to your Gear Inventory.**\n\n"
                    "What is the **Item Name & Model**?\n"
                    "*(e.g., Sony FX6 Body, Canon 24-70mm f/2.8, Aputure 600d Pro, DJI RS3 Pro)*"
                )
            }

        if "category" not in slots or not slots["category"] or slots["category"] == "Other":
            guessed_cat = self._extract_gear_category(slots["name"].lower())
            if guessed_cat != "Other":
                slots["category"] = guessed_cat
            else:
                return {
                    "status": "inquiry",
                    "action": "ask_gear_category",
                    "message": (
                        f"📁 What category does **{slots['name']}** belong to?\n\n"
                        f"Choose: **Camera**, **Lens**, **Lighting**, **Audio**, **Grip**, **Drone**, or **Accessories**"
                    )
                }

        # Apply defaults for optional fields if not given
        category = slots.get("category", "Camera")
        name = slots.get("name", "Production Gear Item")
        quantity = slots.get("quantity", 1)
        location = slots.get("location", "Studio Vault")
        serial = slots.get("serial", "N/A")
        model = slots.get("model", name)

        # Execute creation in ProductionEngine
        item_data = {
            "category": category,
            "name": name,
            "model": model,
            "serial": serial,
            "location": location,
            "quantity": quantity,
            "status": "Available",
            "notes": "Added via Saurabh Patil AI Production Desk"
        }

        saved_item = self.engine.equipment.add_or_update_item(item_data)
        self.engine.save()
        self.reset_state()

        msg = (
            f"🎉 **Gear Successfully Added to Inventory!**\n\n"
            f"• **Item ID**: `{saved_item['id']}`\n"
            f"• **Item Name**: **{saved_item['name']}**\n"
            f"• **Category**: {saved_item['category']}\n"
            f"• **Quantity**: {saved_item['quantity']} unit(s) (Status: 🟢 **Available**)\n"
            f"• **Storage Location**: {saved_item['location']}\n"
            f"• **Serial Number**: {saved_item.get('serial', 'N/A')}\n\n"
            f"📊 *Master Excel Tracker (`Production_Master_Tracker_2026.xlsx`) updated in real-time!*\n\n"
            f"👉 *What would you like to do next? (Add another item, check out gear, or create a call sheet?)*"
        )
        return {"status": "success", "action": "add_gear_done", "message": msg, "data": saved_item}

    def _extract_gear_category(self, text: str) -> str:
        if any(w in text for w in ["camera", "fx6", "fx3", "a7s", "red", "arri", "blackmagic", "body"]):
            return "Camera"
        elif any(w in text for w in ["lens", "lenses", "prime", "zoom", "24-70", "70-200", "50mm", "35mm", "85mm"]):
            return "Lens"
        elif any(w in text for w in ["light", "aputure", "godox", "nanlite", "softbox", "led", "panel", "spotlight"]):
            return "Lighting"
        elif any(w in text for w in ["audio", "mic", "rode", "sennheiser", "lav", "wireless", "boom", "recorder", "zoom f"]):
            return "Audio"
        elif any(w in text for w in ["grip", "gimbal", "tripod", "c-stand", "stand", "slider", "dji rs", "ronin"]):
            return "Grip"
        elif any(w in text for w in ["drone", "mavic", "dji inspire", "fpv", "avata"]):
            return "Drone"
        elif any(w in text for w in ["monitor", "battery", "v-mount", "card", "cfexpress", "sd card", "teradek", "cable"]):
            return "Accessories"
        return "Other"

    # ----------------------------------------------------
    # 2. EQUIPMENT DISPATCH / CHECK-OUT
    # ----------------------------------------------------
    def _init_checkout(self, p: str, low: str, state: Dict[str, Any]) -> Dict[str, Any]:
        slots = {}
        # Try extract crew
        crew_m = re.search(r'\bto\s+([A-Za-z\s]+?)(?=\s+for|\s+until|\s+on|\s+with|$)', p, re.IGNORECASE)
        if crew_m:
            slots["assigned_crew"] = crew_m.group(1).strip()

        # Try extract project
        proj_m = re.search(r'\bfor\s+([A-Za-z0-9\s]+?)(?=\s+until|\s+on|\s+to|\s+with|$)', p, re.IGNORECASE)
        if proj_m:
            slots["project_name"] = proj_m.group(1).strip()

        # Try extract return date
        until_m = re.search(r'\buntil\s+([A-Za-z0-9\s\-]+?)(?=$|\.)', p, re.IGNORECASE)
        if until_m:
            slots["expected_return"] = until_m.group(1).strip()

        # Try match items from current inventory
        inv = self.engine.equipment.get_inventory()
        selected_ids = []
        for it in inv:
            name_parts = it.get("name", "").lower().split()
            id_str = it.get("id", "").lower()
            if id_str in low or any(part in low for part in name_parts if len(part) > 3):
                selected_ids.append(it.get("id"))
        if selected_ids:
            slots["item_ids"] = selected_ids

        state["active_intent"] = "checkout"
        state["slots"] = slots

        return self._continue_checkout(p, low, state, is_init=True)

    def _continue_checkout(self, p: str, low: str, state: Dict[str, Any], is_init: bool = False) -> Dict[str, Any]:
        slots = state.get("slots", {})

        if not is_init:
            if "project_name" not in slots:
                slots["project_name"] = p.strip()
            elif "assigned_crew" not in slots:
                slots["assigned_crew"] = p.strip()
            elif "item_ids" not in slots:
                # Find mentioned items or IDs
                inv = self.engine.equipment.get_inventory()
                found = []
                for it in inv:
                    if it.get("id", "").lower() in low or it.get("name", "").lower() in low:
                        found.append(it.get("id"))
                slots["item_ids"] = found if found else [p.strip()]
            elif "expected_return" not in slots:
                slots["expected_return"] = p.strip()

        if "project_name" not in slots or not slots["project_name"]:
            return {
                "status": "inquiry",
                "action": "ask_checkout_project",
                "message": (
                    "📦 **Let's prepare the Equipment Check-Out (Dispatch).**\n\n"
                    "What is the **Project / Shoot Name**?\n"
                    "*(e.g., Tata Safari Commercial, Godrej Ad, Brand Film)*"
                )
            }

        if "assigned_crew" not in slots or not slots["assigned_crew"]:
            return {
                "status": "inquiry",
                "action": "ask_checkout_crew",
                "message": (
                    f"👤 Who is the **Assigned Crew Member (DOP / Assistant / Camera Operator)** responsible for the gear on **{slots['project_name']}**?"
                )
            }

        if "item_ids" not in slots or not slots["item_ids"]:
            avail = [it for it in self.engine.equipment.get_inventory() if it.get("status") == "Available"]
            avail_preview = ", ".join([f"`{it['id']}` ({it['name']})" for it in avail[:4]]) if avail else "None currently registered"
            return {
                "status": "inquiry",
                "action": "ask_checkout_items",
                "message": (
                    f"🎥 Which equipment items are being dispatched?\n\n"
                    f"Available Gear Preview: {avail_preview}\n\n"
                    f"*(You can type item names like 'Sony FX6 and 24-70mm' or specific Item IDs)*"
                )
            }

        # Apply defaults
        project_name = slots.get("project_name", "Commercial Production")
        assigned_crew = slots.get("assigned_crew", "Lead DOP")
        item_ids = slots.get("item_ids", [])
        expected_return = slots.get("expected_return") or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        log = self.engine.equipment.checkout_equipment(
            project_name=project_name,
            assigned_crew=assigned_crew,
            item_ids=item_ids,
            expected_return=expected_return,
            condition_out="Good / Tested",
            notes="Dispatched via Saurabh Patil AI Assistant"
        )
        self.engine.save()
        self.reset_state()

        msg = (
            f"✅ **Equipment Dispatched & Logged!**\n\n"
            f"• **Dispatch ID**: `{log['id']}`\n"
            f"• **Project / Shoot**: **{log['project_name']}**\n"
            f"• **Assigned To**: {log['assigned_crew']}\n"
            f"• **Dispatched Items**: {log['items_summary']}\n"
            f"• **Expected Return**: 📅 **{log['expected_return']}**\n"
            f"• **Status**: 🟡 **Active Out on Field**\n\n"
            f"Restock & Excel synchronization completed. What else would you like to manage?"
        )
        return {"status": "success", "action": "checkout_done", "message": msg, "data": log}

    # ----------------------------------------------------
    # 3. EQUIPMENT RETURN / CHECK-IN
    # ----------------------------------------------------
    def _init_checkin(self, p: str, low: str, state: Dict[str, Any]) -> Dict[str, Any]:
        slots = {}
        disp_m = re.search(r'(DISP-[\w\-]+)', p, re.IGNORECASE)
        if disp_m:
            slots["dispatch_id"] = disp_m.group(1).upper()

        if any(w in low for w in ["damage", "broken", "issue", "scratch", "lost", "missing", "fault"]):
            slots["condition"] = "Reported Issues"
            slots["notes"] = p
        else:
            slots["condition"] = "Good / Clean"

        state["active_intent"] = "checkin"
        state["slots"] = slots

        return self._continue_checkin(p, low, state, is_init=True)

    def _continue_checkin(self, p: str, low: str, state: Dict[str, Any], is_init: bool = False) -> Dict[str, Any]:
        slots = state.get("slots", {})
        active_logs = [l for l in self.engine.equipment.get_logs() if l.get("status") == "Active Out"]

        if not is_init:
            if "dispatch_id" not in slots:
                disp_m = re.search(r'(DISP-[\w\-]+)', p, re.IGNORECASE)
                if disp_m:
                    slots["dispatch_id"] = disp_m.group(1).upper()
                else:
                    # Match by project name among active logs
                    for l in active_logs:
                        if l.get("project_name", "").lower() in low:
                            slots["dispatch_id"] = l.get("id")
                            break
                    if "dispatch_id" not in slots and active_logs:
                        slots["dispatch_id"] = active_logs[0].get("id")

        if not active_logs:
            self.reset_state()
            return {
                "status": "info",
                "action": "no_active_dispatches",
                "message": "📦 **All equipment is currently checked in and resting in vault!** There are no active dispatches on the field."
            }

        if "dispatch_id" not in slots or not slots["dispatch_id"]:
            log_options = "\n".join([f"• `{l['id']}` — **{l['project_name']}** (Crew: {l['assigned_crew']}, Items: {l['items_summary']})" for l in active_logs[:5]])
            return {
                "status": "inquiry",
                "action": "ask_checkin_id",
                "message": (
                    f"📥 **Which active dispatch is returning?**\n\n"
                    f"Active Dispatches on Field:\n{log_options}\n\n"
                    f"*(Reply with the Dispatch ID or Project Name)*"
                )
            }

        disp_id = slots["dispatch_id"]
        condition = slots.get("condition", "Good / Clean")
        notes = slots.get("notes", "Checked in via Saurabh Patil AI Assistant")

        res = self.engine.equipment.checkin_equipment(
            dispatch_id=disp_id,
            condition_in=condition,
            damaged_or_missing_notes=notes if condition != "Good / Clean" else ""
        )
        self.engine.save()
        self.reset_state()

        if not res:
            return {"status": "error", "message": f"❌ Dispatch record `{disp_id}` could not be found."}

        msg = (
            f"📦 **Equipment Return Recorded & Restocked!**\n\n"
            f"• **Dispatch ID**: `{disp_id}`\n"
            f"• **Return Status**: 🟢 **{res['status']}**\n"
            f"• **Inspected Condition**: {res['condition_in']}\n"
            f"• **Inventory Status**: All items returned to 🟢 **Available** in Studio Vault.\n\n"
            f"Master spreadsheet updated! Is there anything else you need to update?"
        )
        return {"status": "success", "action": "checkin_done", "message": msg, "data": res}

    # ----------------------------------------------------
    # 4. SHOOT BRIEFS & CALL SHEETS
    # ----------------------------------------------------
    def _init_brief(self, p: str, low: str, state: Dict[str, Any]) -> Dict[str, Any]:
        slots = {}
        proj_m = re.search(r'for\s+([A-Za-z0-9\s]+?)(?=\s+on|\s+at|\s+with|\s+call|$)', p, re.IGNORECASE)
        if proj_m:
            slots["project_name"] = proj_m.group(1).strip()

        loc_m = re.search(r'at\s+([A-Za-z0-9\s,]+?)(?=\s+on|\s+call|\s+with|$)', p, re.IGNORECASE)
        if loc_m:
            slots["location"] = loc_m.group(1).strip()

        call_m = re.search(r'call(?:\s+time)?\s*[:\-]?\s*([0-9\:\sAPMapm]+)', p, re.IGNORECASE)
        if call_m:
            slots["call_time"] = call_m.group(1).strip()

        state["active_intent"] = "brief"
        state["slots"] = slots

        return self._continue_brief(p, low, state, is_init=True)

    def _continue_brief(self, p: str, low: str, state: Dict[str, Any], is_init: bool = False) -> Dict[str, Any]:
        slots = state.get("slots", {})

        if not is_init:
            if "project_name" not in slots:
                slots["project_name"] = p.strip()
            elif "shoot_date" not in slots:
                slots["shoot_date"] = p.strip()
            elif "location" not in slots:
                slots["location"] = p.strip()

        if "project_name" not in slots or not slots["project_name"]:
            return {
                "status": "inquiry",
                "action": "ask_brief_project",
                "message": (
                    "🎯 **Let's create a new Shoot Brief & Production Call Sheet.**\n\n"
                    "What is the **Project / Commercial Shoot Name & Client**?\n"
                    "*(e.g., Godrej Ad Commercial / Agency XYZ)*"
                )
            }

        if "shoot_date" not in slots or not slots["shoot_date"]:
            return {
                "status": "inquiry",
                "action": "ask_brief_date",
                "message": (
                    f"📅 What is the **Shoot Date & Call Time** for **{slots['project_name']}**?\n"
                    f"*(e.g., Tomorrow at 06:30 AM or 15 Aug 2026)*"
                )
            }

        if "location" not in slots or not slots["location"]:
            return {
                "status": "inquiry",
                "action": "ask_brief_location",
                "message": (
                    f"📍 Where is the **Shoot Location & Nearest Emergency Hospital**?\n"
                    f"*(e.g., Film City Studio 4, Goregaon / Lifeline Hospital)*"
                )
            }

        # Apply defaults & smart parsing
        project_name = slots.get("project_name", "Commercial Film Shoot")
        client = slots.get("client", "Client / Agency")
        contact_person = slots.get("contact_person", "Client Contact Person")
        deliverables = slots.get("deliverables", "Shoot Coverage & High-Res Deliverables")
        
        raw_date = slots.get("shoot_date", "")
        call_time = slots.get("call_time", "07:00 AM")
        if "at" in raw_date.lower() or re.search(r'\d+\s*(?:am|pm)', raw_date, re.IGNORECASE):
            time_m = re.search(r'(\d+(?:\:\d+)?\s*(?:am|pm))', raw_date, re.IGNORECASE)
            if time_m:
                call_time = time_m.group(1).strip()
            raw_date = re.sub(r'at\s+\d+(?:\:\d+)?\s*(?:am|pm)?', '', raw_date, flags=re.IGNORECASE).strip()
        shoot_date = raw_date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        raw_loc = slots.get("location", "Studio Location")
        hospital = slots.get("hospital", "Nearest General Hospital Emergency")
        if "/" in raw_loc:
            parts = raw_loc.split("/", 1)
            raw_loc = parts[0].strip()
            hospital = parts[1].strip()
        location = raw_loc

        brief_data = {
            "project_name": project_name,
            "client": client,
            "contact_person": contact_person,
            "deliverables": deliverables,
            "shoot_date": shoot_date,
            "call_time": call_time,
            "location": location,
            "hospital": hospital,
            "key_contacts": "Saurabh Patil - Production Manager",
            "concept": deliverables,
            "status": "Active"
        }

        b = self.engine.briefs.create_brief(brief_data)
        self.engine.save()
        self.reset_state()

        msg = (
            f"🎯 **Shoot Added to Shoot Tracker!**\n\n"
            f"• **Shoot Ref**: `{b['id']}`\n"
            f"• **Project Name**: **{b['project_name']}**\n"
            f"• **Client & Contact Person**: {b['client']} ({b['contact_person']})\n"
            f"• **Deliverables**: <span style=\"color: #38bdf8;\">{b['deliverables']}</span>\n"
            f"• **Shoot Date**: 📅 {b['shoot_date']}\n"
            f"• **Call Time**: ⏰ {b['call_time']}\n"
            f"• **Location**: 📍 {b['location']}\n"
            f"• **Status**: 🟢 **{b['status']}**\n\n"
            f"📄 **Actions**:\n"
            f"• View & Print: [Open Printable Call Sheet](/api/brief/print/{b['id']})\n"
            f"• Download: [Download Call Sheet HTML](/api/brief/download/{b['id']})\n\n"
            f"Synchronized with `Production_Master_Tracker_2026.xlsx`! What else would you like to add?"
        )
        return {"status": "success", "action": "brief_done", "message": msg, "data": b}

    def _handle_delete_shoot(self, p: str, low: str) -> Dict[str, Any]:
        shoot_m = re.search(r'(SHOOT-[\w\-]+)', p, re.IGNORECASE)
        briefs = self.engine.briefs.get_all_briefs()
        target_id = None
        target_name = ""

        if shoot_m:
            target_id = shoot_m.group(1).upper()
        else:
            for b in briefs:
                if b.get("project_name", "").lower() in low or b.get("client", "").lower() in low:
                    target_id = b.get("id")
                    target_name = b.get("project_name")
                    break

        if not target_id and briefs:
            target_id = briefs[0].get("id")
            target_name = briefs[0].get("project_name")

        if not target_id:
            return {"status": "info", "message": "📦 No shoots currently exist in Shoot Tracker to delete."}

        success = self.engine.briefs.delete_brief(target_id)
        if success:
            self.engine.save()
            return {
                "status": "success",
                "action": "delete_shoot",
                "message": f"🗑️ **Shoot `{target_id}` {f'({target_name})' if target_name else ''} has been removed from Shoot Tracker and Master Spreadsheet!**"
            }
        return {"status": "error", "message": f"❌ Could not find shoot record `{target_id}` to delete."}

    def _handle_whatsapp_share(self, p: str, low: str) -> Dict[str, Any]:
        briefs = self.engine.briefs.get_all_briefs()
        if not briefs:
            return {"status": "info", "message": "📦 No shoots currently exist in Shoot Tracker to share."}

        target = briefs[0]
        shoot_m = re.search(r'(SHOOT-[\w\-]+)', p, re.IGNORECASE)
        if shoot_m:
            for b in briefs:
                if b.get("id", "").upper() == shoot_m.group(1).upper():
                    target = b
                    break
        else:
            for b in briefs:
                if b.get("project_name", "").lower() in low or b.get("client", "").lower() in low:
                    target = b
                    break

        import urllib.parse
        loc = target.get("location", "")
        maps_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(loc)}" if loc else ""
        
        equip = target.get('equipment_manifest') or target.get('equipment_for_shoot') or 'Cameras, Lenses, Flashes & Kit'
        wa_text = (
            f"🎬 *PRODUCTION CALL SHEET & SHOOT BRIEF*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Project:* {target.get('project_name')}\n"
            f"🏢 *Client:* {target.get('client')}\n"
            f"👤 *Client POC:* {target.get('contact_person', target.get('client'))}\n"
            f"📦 *Deliverables:* {target.get('deliverables') or 'Shoot Coverage'}\n"
            f"📅 *Shoot Date:* {target.get('shoot_date')}\n"
            f"⏰ *Call Time:* {target.get('call_time')}\n"
            f"📍 *Location:* {target.get('location')}\n"
            f"🗺️ *Google Maps:* {maps_link}\n"
            f"👥 *Crew / Team:* {target.get('cast_talent') or target.get('key_contacts')}\n"
            f"🎥 *Equipment for Shoot:* {equip}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 *Production Manager:* Saurabh Patil\n"
            f"⚠️ *Please report on time. Have a safe shoot!*"
        )
        
        encoded = urllib.parse.quote(wa_text)
        wa_url = f"https://api.whatsapp.com/send?text={encoded}"
        
        msg = (
            f"📲 **Ready WhatsApp Message for {target.get('project_name')} (`{target.get('id')}`):**\n\n"
            f"```text\n{wa_text}\n```\n\n"
            f"👉 **[Click Here to Open WhatsApp & Share]({wa_url})**\n"
            f"*(Or copy the text above and paste directly into your WhatsApp crew or client group!)*"
        )
        return {"status": "success", "action": "whatsapp_share", "message": msg, "data": target}

    def _handle_edit_shoot(self, p: str, low: str) -> Dict[str, Any]:
        briefs = self.engine.briefs.get_all_briefs()
        if not briefs:
            return {"status": "info", "message": "📦 No shoots currently exist in Shoot Tracker to edit."}

        target = briefs[0]
        shoot_m = re.search(r'(SHOOT-[\w\-]+)', p, re.IGNORECASE)
        if shoot_m:
            for b in briefs:
                if b.get("id", "").upper() == shoot_m.group(1).upper():
                    target = b
                    break
        else:
            for b in briefs:
                if b.get("project_name", "").lower() in low or b.get("client", "").lower() in low:
                    target = b
                    break

        # Check Same-Day Edit Rule
        if not self.engine.briefs.is_editable(target):
            created_date = target.get("created_date") or target.get("shoot_date")
            return {
                "status": "error",
                "message": f"🔒 **Editing Locked**: Changes for `{target.get('id')}` are only accepted on the date of entry (*{created_date}*). Next-day edits are locked for production integrity."
            }

        updates = {}
        # Check call time
        time_m = re.search(r'(?:call(?:\s+time)?|reach(?:\s+time)?|time)\s*(?:to|is|=)?\s*([0-9]{1,2}(?:\:[0-9]{2})?\s*(?:am|pm)?)', p, re.IGNORECASE)
        if time_m:
            updates["call_time"] = time_m.group(1).strip()

        # Check location
        loc_m = re.search(r'(?:location|venue|at)\s*(?:to|is|=)?\s*([A-Za-z0-9\s\,\.\-]+?)(?:\s+for|\s+on|\.|$)', p, re.IGNORECASE)
        if loc_m and "time" not in loc_m.group(1).lower() and "shoot" not in loc_m.group(1).lower():
            updates["location"] = loc_m.group(1).strip()

        # Check deliverables
        deliv_m = re.search(r'deliverables?\s*(?:to|is|=)?\s*([^\n\.\,]+)', p, re.IGNORECASE)
        if deliv_m:
            updates["deliverables"] = deliv_m.group(1).strip()

        if not updates:
            return {
                "status": "inquiry",
                "message": (
                    f"✏️ **Editing `{target.get('id')}` ({target.get('project_name')}) - Same-Day Window Active**\n\n"
                    f"What would you like to update? (e.g., *'Change call time to 09:00 AM'*, *'Change location to JW Marriott'*, or *'Update deliverables to 60 photos'*)"
                )
            }

        ok, msg, updated = self.engine.briefs.update_brief(target.get("id"), updates)
        if ok:
            self.engine.save()
            return {
                "status": "success",
                "action": "shoot_updated",
                "message": (
                    f"✅ **Shoot `{target.get('id')}` Updated Successfully!**\n\n"
                    f"• **Project**: **{updated.get('project_name')}**\n"
                    f"• **Call Time**: ⏰ **{updated.get('call_time')}**\n"
                    f"• **Location**: 📍 **{updated.get('location')}**\n"
                    f"• **Deliverables**: <span style=\"color: #38bdf8;\">{updated.get('deliverables')}</span>\n\n"
                    f"Master Spreadsheet synchronized!"
                ),
                "data": updated
            }
        return {"status": "error", "message": f"❌ {msg}"}

    def _handle_update_shoot_status(self, p: str, low: str) -> Dict[str, Any]:
        briefs = self.engine.briefs.get_all_briefs()
        if not briefs:
            return {"status": "info", "message": "📦 No shoots currently exist in Shoot Tracker to update status."}

        target = briefs[0]
        shoot_m = re.search(r'(SHOOT-[\w\-]+|\b\d+\b)', p, re.IGNORECASE)
        if shoot_m:
            query = shoot_m.group(1).upper()
            for b in briefs:
                if b.get("id", "").upper() == query or b.get("id", "").endswith(query):
                    target = b
                    break
        else:
            for b in briefs:
                if b.get("project_name", "").lower() in low or b.get("client", "").lower() in low:
                    target = b
                    break

        # Detect desired status
        new_status = None
        if "wrapped" in low or "wrap" in low:
            new_status = "Wrapped"
        elif "completed" in low or "complete" in low or "delivered" in low or "finish" in low or "done" in low:
            new_status = "Completed"
        elif "in progress" in low or "rolling" in low:
            new_status = "In Progress"
        elif "scheduled" in low or "upcoming" in low:
            new_status = "Scheduled"
        elif "post-production" in low or "post production" in low or "post" in low:
            new_status = "Post-Production"
        elif "postponed" in low or "delay" in low:
            new_status = "Postponed"
        elif "cancelled" in low or "canceled" in low:
            new_status = "Cancelled"
        elif "active" in low:
            new_status = "Active"

        if not new_status:
            return {
                "status": "inquiry",
                "message": (
                    f"🎯 **Select Status for Shoot `{target.get('id')}` ({target.get('project_name')}):**\n\n"
                    f"Current Status: **{target.get('status', 'Active')}**\n"
                    f"Available Options: *Active*, *Scheduled*, *In Progress*, *Wrapped*, *Post-Production*, *Completed*, *Postponed*, *Cancelled*.\n\n"
                    f"Which status would you like to set?"
                )
            }

        ok, msg, updated = self.engine.briefs.update_status(target.get("id"), new_status)
        if ok:
            self.engine.save()
            return {
                "status": "success",
                "action": "status_updated",
                "message": (
                    f"✨ **Status for Shoot `{target.get('id')}` ({target.get('project_name')}) Updated to `{new_status}`!**\n\n"
                    f"Master Excel Spreadsheet (`Production_Master_Tracker_2026.xlsx`) synchronized."
                ),
                "data": updated
            }
        return {"status": "error", "message": f"❌ {msg}"}

    # ----------------------------------------------------
    # 5. PETTY CASH & EXPENSES
    # ----------------------------------------------------
    def _init_expense(self, p: str, low: str, state: Dict[str, Any]) -> Dict[str, Any]:
        slots = {}
        # Extract amount
        amt_m = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:[,\.]\d+)?)\s*(?:₹|rs|inr|rupees)?', p, re.IGNORECASE)
        if amt_m:
            raw_amt = amt_m.group(1).replace(",", "")
            try:
                slots["amount"] = float(raw_amt)
            except ValueError:
                pass

        # Extract category
        slots["category"] = self._extract_expense_category(low)

        # Extract description
        desc_m = re.search(r'(?:for|on|desc|item)\s+([A-Za-z0-9\s\-]+?)(?=\s+(?:paid|via|by|upi|cash|card)|$)', p, re.IGNORECASE)
        if desc_m and len(desc_m.group(1).strip()) > 2:
            slots["description"] = desc_m.group(1).strip()

        state["active_intent"] = "expense"
        state["slots"] = slots

        return self._continue_expense(p, low, state, is_init=True)

    def _continue_expense(self, p: str, low: str, state: Dict[str, Any], is_init: bool = False) -> Dict[str, Any]:
        slots = state.get("slots", {})

        if not is_init:
            if "amount" not in slots:
                amt_m = re.search(r'(\d+(?:[,\.]\d+)?)', p)
                if amt_m:
                    slots["amount"] = float(amt_m.group(1).replace(",", ""))
            if "description" not in slots:
                slots["description"] = p.strip()
            if "category" not in slots or slots["category"] == "Miscellaneous":
                cat = self._extract_expense_category(low)
                if cat != "Miscellaneous":
                    slots["category"] = cat

        if "amount" not in slots or not slots["amount"]:
            return {
                "status": "inquiry",
                "action": "ask_expense_amount",
                "message": (
                    "💰 **Let's log a Production Expense / Petty Cash entry.**\n\n"
                    "What is the **Expense Amount (₹)** and **Purpose**?\n"
                    "*(e.g., ₹3,500 for generator fuel, ₹1,200 for crew snacks)*"
                )
            }

        if "description" not in slots or not slots["description"]:
            return {
                "status": "inquiry",
                "action": "ask_expense_desc",
                "message": (
                    f"📝 What was the expense of **₹{slots['amount']:,.2f}** for?\n"
                    f"*(e.g., Taxi fare for DOP, Art department props, Crew lunch)*"
                )
            }

        amount = slots.get("amount", 0.0)
        category = slots.get("category") or self._extract_expense_category(slots["description"].lower())
        description = slots.get("description", "On-set production expense")
        project_name = slots.get("project_name", "General Production")
        paid_by = slots.get("paid_by", "Saurabh Patil (PM)")
        mode = "UPI" if "upi" in low or "gpay" in low or "phonepe" in low else ("Cash" if "cash" in low else "UPI")

        exp = self.engine.expenses.log_expense({
            "project_name": project_name,
            "category": category,
            "description": description,
            "amount": amount,
            "paid_by": paid_by,
            "mode": mode,
            "status": "Approved"
        })
        self.engine.save()
        self.reset_state()

        msg = (
            f"💰 **Production Expense Logged!**\n\n"
            f"• **Expense Ref**: `{exp['id']}`\n"
            f"• **Amount**: **₹{exp['amount']:,.2f}**\n"
            f"• **Category**: {exp['category']}\n"
            f"• **Description**: {exp['description']}\n"
            f"• **Payment Mode**: {exp['mode']} (Paid by: {exp['paid_by']})\n\n"
            f"📊 *Updated live in `Production_Master_Tracker_2026.xlsx`!*\n\n"
            f"💡 *Tip: You can attach photo receipts anytime in the Petty Cash tab or via Ctrl+V paste.*"
        )
        return {"status": "success", "action": "expense_done", "message": msg, "data": exp}

    def _extract_expense_category(self, text: str) -> str:
        if any(w in text for w in ["fuel", "diesel", "petrol", "cab", "taxi", "uber", "ola", "transport", "travel", "rickshaw", "auto", "van"]):
            return "Transport & Fuel"
        elif any(w in text for w in ["food", "lunch", "dinner", "breakfast", "snacks", "tea", "coffee", "catering", "water", "meal"]):
            return "Food & Catering"
        elif any(w in text for w in ["prop", "art", "costume", "dress", "makeup", "set dressing", "flowers", "paint"]):
            return "Art & Props"
        elif any(w in text for w in ["rental", "studio", "location", "permit", "police", "permission", "generator"]):
            return "Location & Permits"
        elif any(w in text for w in ["lens rent", "camera rent", "light rent", "equipment rent", "hire"]):
            return "Equipment Rental"
        return "Miscellaneous"

    # ----------------------------------------------------
    # 6. INVENTORY QUERY & SUMMARY
    # ----------------------------------------------------
    def _handle_inventory_query(self, low: str) -> Dict[str, Any]:
        category = None
        if "camera" in low:
            category = "Camera"
        elif "lens" in low or "lenses" in low:
            category = "Lens"
        elif "light" in low:
            category = "Lighting"
        elif "audio" in low or "mic" in low:
            category = "Audio"
        elif "grip" in low or "gimbal" in low or "tripod" in low:
            category = "Grip"
        elif "drone" in low:
            category = "Drone"

        items = self.engine.equipment.get_inventory(category=category)
        if not items:
            return {
                "status": "info",
                "action": "query_inventory",
                "message": (
                    "📦 **Your inventory currently has 0 items registered.**\n\n"
                    "Would you like me to help you add your gear list right now? Just type:\n"
                    "👉 *'Add gear: Sony FX6 Body, category Camera'*"
                ),
                "data": []
            }

        lines = [f"🎥 **Found {len(items)} items in Gear Inventory:**\n"]
        for it in items:
            badge = "🟢 Available" if it.get("status") == "Available" else f"🟡 {it.get('status')}"
            lines.append(f"• **[{it.get('id')}]** {it.get('name')} — {badge} (Loc: {it.get('location', 'Vault')})")

        lines.append("\n👉 *Need to check out any of this gear for a shoot or add new items? Let me know!*")
        return {
            "status": "success",
            "action": "query_inventory",
            "message": "\n".join(lines),
            "data": items
        }

    def _handle_summary(self) -> Dict[str, Any]:
        summary = self.engine.get_dashboard_summary()
        eq = summary["equipment"]
        exp = summary["expenses"]
        briefs = summary.get("total_briefs", len(self.engine.briefs.get_all_briefs()))

        msg = (
            f"🎬 **Production Manager OS — Live Overview (Saurabh Patil Desk)**\n"
            f"📅 **Date**: {datetime.now().strftime('%d %b %Y')}\n\n"
            f"• 🎥 **Inventory Status**: {eq['total_items']} items registered | "
            f"🟢 **{eq['available_items']} Available** | 🟡 **{eq['in_use_items']} In Use** | 🔴 {eq['maintenance_items']} Maintenance\n"
            f"• 📦 **Active Dispatches**: {eq['active_dispatches']} active on field\n"
            f"• 🎯 **Shoot Call Sheets**: {briefs} briefs generated\n"
            f"• 💰 **Petty Cash Spent**: ₹{exp['total_expenses']:,.2f} across {exp['transaction_count']} receipts\n\n"
            f"📊 All sheets synchronized with `Production_Master_Tracker_2026.xlsx`.\n"
            f"👉 *What would you like to create, update, or add?*"
        )
        return {"status": "success", "action": "summary", "message": msg, "data": summary}

    def _try_smart_match(self, p: str, low: str, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # 1. Raw shoot note / WhatsApp message detection
        has_loc = any(w in low for w in ["location-", "location:", "location -"]) or ("location" in low and ("hotel" in low or "studio" in low or "kharadi" in low or "pune" in low or "mumbai" in low))
        has_time = any(w in low for w in ["time-", "time:", "time -", "reach location", "call time", "8.30", "8:30", "9:00", "7:00"])
        has_team = any(w in low for w in ["team member", "team:", "team -", "crew:", "crew -", "akash", "photographer"])
        has_shoot = any(w in low for w in ["shoot type", "event photography", "photography", "videography", "corporate shoot"])

        if (has_loc and (has_time or has_team or has_shoot)) or (has_shoot and (has_time or has_loc)) or (has_team and has_loc):
            return self._parse_raw_shoot_note(p, low, state)

        # 2. If user explicitly specifies a complete gear addition like "Sony FX6 category camera"
        if any(cat in low for cat in ["camera", "lens", "lighting", "audio", "grip", "drone"]) and any(act in low for act in ["add", "new", "register"]):
            return self._init_add_gear(p, low, state)
        
        # 3. If user specifies amount and description like "5000 for studio rent"
        if re.search(r'\d+\s*(?:rs|inr|rupees)?\s+(?:for|on)\s+', low):
            return self._init_expense(p, low, state)

        return None

    def _parse_raw_shoot_note(self, p: str, low: str, state: Dict[str, Any]) -> Dict[str, Any]:
        # Extract Date
        date_m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', p, re.IGNORECASE)
        shoot_date = date_m.group(1).strip() if date_m else datetime.now().strftime("%d %b %Y")

        # Extract Time
        time_m = re.search(r'(?:time\s*[\-:]\s*)?(\d{1,2}(?:[\.:]\d{2})?\s*(?:am|pm))', p, re.IGNORECASE)
        call_time = time_m.group(1).upper().replace(".", ":") if time_m else "08:30 AM"

        # Extract Location
        loc_m = re.search(r'location\s*[\-:]\s*([^\n\r]+)', p, re.IGNORECASE)
        location = loc_m.group(1).strip() if loc_m else "Radisson Blu Hotel, Kharadi"

        # Extract Shoot Type / Concept
        shoot_m = re.search(r'shoot\s*type\s*[\-:]\s*([^\n\r]+)', p, re.IGNORECASE)
        shoot_type = shoot_m.group(1).strip() if shoot_m else "Event Photography"

        # Extract Team Members with Official Team Matcher
        assigned_crew_list = []
        for member in OFFICIAL_TEAM_MEMBERS:
            first_name = member.split()[0].lower()
            last_name = member.split()[-1].lower()
            if first_name in p.lower() or last_name in p.lower():
                assigned_crew_list.append(member)

        team_m = re.search(r'team\s*member[s]?\s*[\-:]\s*([^\n\r]+)', p, re.IGNORECASE)
        if team_m:
            raw_team = team_m.group(1).strip()
            # If explicit team line, also check members
            for member in OFFICIAL_TEAM_MEMBERS:
                if member.split()[0].lower() in raw_team.lower() and member not in assigned_crew_list:
                    assigned_crew_list.append(member)
            if not assigned_crew_list:
                assigned_crew_list = [raw_team]

        team_members = ", ".join(assigned_crew_list) if assigned_crew_list else "Akash Deshmukh, Samyak Chavhan"

        # Extract Client / Contact Person
        client_name = "Eaton India"
        contact_person = "Eaton Contact Person"
        for line in p.splitlines():
            line_str = line.strip()
            if "contact person" in line_str.lower() or "eaton" in line_str.lower():
                if "eaton" in line_str.lower():
                    client_name = "Eaton India"
                contact_person = line_str

        project_name = f"Eaton - {shoot_type}"
        deliverables = f"{shoot_type} Coverage (Edited Deliverables + High-Res Photo Export)"

        # Hospital emergency nearby
        hospital = "Manipal Hospital / Columbia Asia, Kharadi" if "kharadi" in location.lower() else "Nearest General Emergency Hospital"

        brief_data = {
            "project_name": project_name,
            "client": client_name,
            "contact_person": contact_person,
            "deliverables": deliverables,
            "shoot_date": shoot_date,
            "call_time": call_time,
            "location": location,
            "hospital": hospital,
            "key_contacts": f"Team: {team_members} | Client: {contact_person} | PM: Saurabh Patil",
            "concept": f"{shoot_type} coverage at {location}.",
            "status": "Active"
        }

        b = self.engine.briefs.create_brief(brief_data)
        self.engine.save()
        self.reset_state()

        msg = (
            f"🎯 **Shoot Successfully Added to Shoot Tracker!**\n\n"
            f"• **Shoot Ref**: `{b['id']}`\n"
            f"• **Project Name**: **{b['project_name']}**\n"
            f"• **Client & Contact Person**: **{b['client']}** ({contact_person})\n"
            f"• **Deliverables**: <span style=\"color: #38bdf8;\">{b['deliverables']}</span>\n"
            f"• **Shoot Date**: 📅 **{b['shoot_date']}**\n"
            f"• **Call Time**: ⏰ **{b['call_time']}**\n"
            f"• **Location**: 📍 **{b['location']}**\n"
            f"• **Assigned Crew**: 👤 {team_members}\n"
            f"• **Status**: 🟢 **{b['status']}**\n\n"
            f"📄 **View & Print Documents**:\n"
            f"• [📋 Printable Camera Crew Equipment Checklist](/api/brief/checklist/{b['id']})\n"
            f"• [📄 Official Production Call Sheet](/api/brief/print/{b['id']})\n"
            f"• [📥 Download Call Sheet HTML](/api/brief/download/{b['id']})\n\n"
            f"📊 *Master Excel Tracker (`Production_Master_Tracker_2026.xlsx`) synchronized live!*"
        )
        return {"status": "success", "action": "raw_brief_parsed", "message": msg, "data": b}
