"""
Live Shoot Tracker Manager
Coordinates real-time on-set tracking:
- Scene/Shot/Take Logging (Clapperboard log)
- Live Shoot Milestones & Timecode tracking
- On-Set Equipment packing & verification checklist
- Live Crew Activity Feed
"""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class ShootTrackerManager:
    def __init__(self, data_store: Dict[str, Any]):
        self.data_store = data_store
        
        # Ensure collections exist
        if "shoot_milestones" not in self.data_store:
            self.data_store["shoot_milestones"] = []
        if "shot_logs" not in self.data_store:
            self.data_store["shot_logs"] = []
        if "equipment_checklists" not in self.data_store:
            self.data_store["equipment_checklists"] = {}
        if "activity_feed" not in self.data_store:
            self.data_store["activity_feed"] = []

    def get_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_time_str(self) -> str:
        return datetime.now().strftime("%I:%M %p")

    def log_activity(self, shoot_id: str, crew_name: str, action: str, details: str = "", category: str = "general"):
        """Logs an activity event into the live feed."""
        entry = {
            "id": f"ACT-{int(time.time() * 1000)}",
            "shoot_id": shoot_id,
            "crew_name": crew_name or "Crew Member",
            "action": action,
            "details": details,
            "category": category,
            "timestamp": self.get_timestamp(),
            "time_str": self.get_time_str()
        }
        self.data_store["activity_feed"].insert(0, entry)
        # Keep recent 200 activity logs
        if len(self.data_store["activity_feed"]) > 200:
            self.data_store["activity_feed"] = self.data_store["activity_feed"][:200]
        return entry

    def get_activity_feed(self, shoot_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        feed = self.data_store.get("activity_feed", [])
        if shoot_id:
            feed = [x for x in feed if x.get("shoot_id") == shoot_id or not x.get("shoot_id")]
        return feed[:limit]

    # ----------------------------------------------------
    # Milestones & Live Status
    # ----------------------------------------------------
    def log_milestone(self, shoot_id: str, milestone_type: str, crew_name: str, notes: str = "") -> Dict[str, Any]:
        """
        Milestone types:
        - reached_office: Reached LightPaper Creations Office
        - call_checkin: Crew Call Check-in / Reached Set Location
        - setup_complete: Base Camp / Camera Setup Ready
        - waiting: Waiting / Standby
        - first_shot: First Shot Rolled
        - lunch_call: Lunch Break Call
        - lunch_resume: Shoot Resumed Post-Lunch
        - wrap_call: Day Wrap Called
        - custom: Custom milestone
        """
        milestone = {
            "id": f"MLS-{int(time.time() * 1000)}",
            "shoot_id": shoot_id,
            "type": milestone_type,
            "label": self._milestone_label(milestone_type),
            "crew_name": crew_name,
            "notes": notes,
            "timestamp": self.get_timestamp(),
            "time_str": self.get_time_str()
        }
        self.data_store["shoot_milestones"].append(milestone)
        
        # Log to activity feed
        self.log_activity(
            shoot_id=shoot_id,
            crew_name=crew_name,
            action=f"Milestone: {milestone['label']}",
            details=notes or f"Marked at {milestone['time_str']}",
            category="milestone"
        )
        return milestone

    def _milestone_label(self, m_type: str) -> str:
        labels = {
            "reached_office": "🏢 Reached LightPaper Office",
            "call_checkin": "📍 Reached Set Location",
            "setup_complete": "⚡ Setup Complete & Ready",
            "waiting": "⏳ Waiting / Standby",
            "first_shot": "🎬 First Shot Rolled",
            "lunch_call": "🍱 Lunch Break Call",
            "lunch_resume": "🔄 Post-Lunch Resumed",
            "wrap_call": "🎉 Final Wrap Called",
            "custom": "📌 Event Note"
        }
        return labels.get(m_type, m_type.replace("_", " ").title())

    def get_milestones(self, shoot_id: str) -> List[Dict[str, Any]]:
        return [m for m in self.data_store.get("shoot_milestones", []) if m.get("shoot_id") == shoot_id]

    # ----------------------------------------------------
    # Live Clapperboard & Shot / Take Logger
    # ----------------------------------------------------
    def log_shot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        shoot_id = data.get("shoot_id", "")
        scene = str(data.get("scene", "1")).strip()
        shot = str(data.get("shot", "1")).strip()
        take = int(data.get("take", 1))
        is_circle = bool(data.get("is_circle", False))
        status = data.get("status", "Good" if is_circle else "NG") # Good, NG, Hold, Cut
        notes = data.get("notes", "")
        crew_name = data.get("crew_name", "Camera Dept")
        camera_roll = data.get("camera_roll", "A001")
        sound_roll = data.get("sound_roll", "S001")

        shot_id = f"SHT-{int(time.time() * 1000)}"
        shot_entry = {
            "id": shot_id,
            "shoot_id": shoot_id,
            "scene": scene,
            "shot": shot,
            "take": take,
            "is_circle": is_circle,
            "status": status,
            "notes": notes,
            "crew_name": crew_name,
            "camera_roll": camera_roll,
            "sound_roll": sound_roll,
            "timestamp": self.get_timestamp(),
            "time_str": self.get_time_str()
        }

        self.data_store["shot_logs"].append(shot_entry)

        # Log activity
        take_status_str = "⭐ Good Take (Circle)" if is_circle or status == "Good" else f"Take ({status})"
        self.log_activity(
            shoot_id=shoot_id,
            crew_name=crew_name,
            action=f"Logged Scene {scene} • Shot {shot} • Take {take}",
            details=f"{take_status_str} {('- ' + notes) if notes else ''}",
            category="shot"
        )
        return shot_entry

    def get_shots(self, shoot_id: str) -> List[Dict[str, Any]]:
        return [s for s in self.data_store.get("shot_logs", []) if s.get("shoot_id") == shoot_id]

    def delete_shot(self, shot_id: str) -> bool:
        logs = self.data_store.get("shot_logs", [])
        for i, s in enumerate(logs):
            if s.get("id") == shot_id:
                del logs[i]
                return True
        return False

    def toggle_circle_take(self, shot_id: str) -> Optional[Dict[str, Any]]:
        for s in self.data_store.get("shot_logs", []):
            if s.get("id") == shot_id:
                s["is_circle"] = not s.get("is_circle", False)
                s["status"] = "Good" if s["is_circle"] else "NG"
                return s
        return None

    # ----------------------------------------------------
    # On-Set Equipment Packing & Verification Checklist
    # ----------------------------------------------------
    def get_shoot_equipment_status(self, shoot_id: str) -> List[Dict[str, Any]]:
        """Returns equipment checklist state for a specific shoot."""
        # Find shoot brief
        brief = None
        for b in self.data_store.get("shoot_briefs", []):
            if b.get("id") == shoot_id:
                brief = b
                break
                
        manifest_str = brief.get("equipment_manifest", "") if brief else ""
        items = [i.strip() for i in manifest_str.split(",") if i.strip()]
        
        saved_status = self.data_store.get("equipment_checklists", {}).get(shoot_id, {})
        
        result = []
        for idx, item_name in enumerate(items):
            item_key = f"item_{idx}_{item_name}"
            state = saved_status.get(item_key, {
                "name": item_name,
                "packed": False,
                "on_set": False,
                "returned": False,
                "damaged": False,
                "damage_notes": "",
                "updated_by": ""
            })
            # Guarantee all fields are present (backward compat with old saved states)
            state.setdefault("packed", False)
            state.setdefault("on_set", False)
            state.setdefault("returned", False)
            state.setdefault("damaged", False)
            state.setdefault("damage_notes", "")
            state["key"] = item_key
            state["item_key"] = item_key
            state["name"] = item_name
            result.append(state)
            
        return result

    def update_equipment_item(self, shoot_id: str, item_key: str, data: Dict[str, Any], crew_name: str) -> Dict[str, Any]:
        if "equipment_checklists" not in self.data_store:
            self.data_store["equipment_checklists"] = {}
        if shoot_id not in self.data_store["equipment_checklists"]:
            self.data_store["equipment_checklists"][shoot_id] = {}
            
        current = self.data_store["equipment_checklists"][shoot_id].get(item_key, {})
        current.update(data)
        current["updated_by"] = crew_name
        current["updated_at"] = self.get_timestamp()
        self.data_store["equipment_checklists"][shoot_id][item_key] = current
        
        # Activity log if status changed
        item_name = data.get("name", item_key)
        status_changes = []
        if "packed" in data:
            status_changes.append("Packed" if data["packed"] else "Unpacked")
        if "on_set" in data:
            status_changes.append("Verified On Set" if data["on_set"] else "Off Set")
        if "returned" in data:
            status_changes.append("Returned to Vault" if data["returned"] else "Pending Return")
        if data.get("damaged"):
            status_changes.append(f"⚠️ FLAGGED DAMAGED: {data.get('damage_notes','')}")
            
        if status_changes:
            self.log_activity(
                shoot_id=shoot_id,
                crew_name=crew_name,
                action=f"Gear Check: {item_name}",
                details=", ".join(status_changes),
                category="gear"
            )
            
        return current
