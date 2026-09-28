"""
User & Employee Authentication Manager
Handles employee logins, passwords, roles, sessions, and permissions.
"""

import hashlib
import secrets
import time
from typing import Dict, List, Any, Optional

DEFAULT_USERS = [
    {
        "id": "USR-001",
        "username": "saurabh",
        "password_hash": hashlib.sha256("shoot2026".encode("utf-8")).hexdigest(),
        "name": "Saurabh Patil",
        "role": "Production Manager",
        "phone": "+91 98230 00000",
        "is_admin": True,
        "avatar_color": "#f59e0b"
    },
    {
        "id": "USR-002",
        "username": "rohit",
        "password_hash": hashlib.sha256("shoot2026".encode("utf-8")).hexdigest(),
        "name": "Rohit Salunke",
        "role": "Director / DOP",
        "phone": "+91 98231 11111",
        "is_admin": False,
        "avatar_color": "#3b82f6"
    },
    {
        "id": "USR-003",
        "username": "akash",
        "password_hash": hashlib.sha256("shoot2026".encode("utf-8")).hexdigest(),
        "name": "Akash Deshmukh",
        "role": "Cinematographer / Gaffer",
        "phone": "+91 98232 22222",
        "is_admin": False,
        "avatar_color": "#10b981"
    },
    {
        "id": "USR-004",
        "username": "samyak",
        "password_hash": hashlib.sha256("shoot2026".encode("utf-8")).hexdigest(),
        "name": "Samyak Chavhan",
        "role": "Sound Recordist / Crew",
        "phone": "+91 98233 33333",
        "is_admin": False,
        "avatar_color": "#8b5cf6"
    },
    {
        "id": "USR-005",
        "username": "vedant",
        "password_hash": hashlib.sha256("shoot2026".encode("utf-8")).hexdigest(),
        "name": "Vedant Mankar",
        "role": "Assistant Director",
        "phone": "+91 98234 44444",
        "is_admin": False,
        "avatar_color": "#ec4899"
    },
    {
        "id": "USR-006",
        "username": "crew",
        "password_hash": hashlib.sha256("shoot2026".encode("utf-8")).hexdigest(),
        "name": "Production Crew",
        "role": "Crew Member",
        "phone": "+91 98235 55555",
        "is_admin": False,
        "avatar_color": "#06b6d4"
    }
]

class UserManager:
    def __init__(self, data_store: Dict[str, Any]):
        self.data_store = data_store
        
        # Ensure default users are up to date with password hashes
        if "users" not in self.data_store or not self.data_store["users"]:
            self.data_store["users"] = list(DEFAULT_USERS)
        else:
            # Sync default user passwords to shoot2026
            for def_u in DEFAULT_USERS:
                found = False
                for u in self.data_store["users"]:
                    if u.get("username", "").lower() == def_u["username"]:
                        u["password_hash"] = def_u["password_hash"]
                        u["name"] = def_u["name"]
                        u["role"] = def_u["role"]
                        found = True
                        break
                if not found:
                    self.data_store["users"].append(def_u)
        
        if "active_sessions" not in self.data_store:
            self.data_store["active_sessions"] = {}
            
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def authenticate(self, username_or_phone: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates user with username or phone and password."""
        ident = username_or_phone.strip().lower()
        pwd_hash = self._hash_password(password)

        for u in self.data_store.get("users", []):
            u_name = u.get("username", "").strip().lower()
            u_phone = u.get("phone", "").replace(" ", "").replace("-", "")
            clean_ident = ident.replace(" ", "").replace("-", "")
            
            if (u_name == ident or u_phone == clean_ident) and u.get("password_hash") == pwd_hash:
                token = secrets.token_hex(24)
                session_data = {
                    "token": token,
                    "user_id": u["id"],
                    "username": u["username"],
                    "name": u["name"],
                    "role": u["role"],
                    "is_admin": u.get("is_admin", False),
                    "avatar_color": u.get("avatar_color", "#3b82f6"),
                    "created_at": time.time(),
                    "expires_at": time.time() + (86400 * 30) # 30 days active session
                }
                self.data_store["active_sessions"][token] = session_data
                return session_data
        return None

    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Checks if session token is valid."""
        if not token:
            return None
        session = self.data_store.get("active_sessions", {}).get(token)
        if not session:
            return None
        if time.time() > session.get("expires_at", 0):
            del self.data_store["active_sessions"][token]
            return None
        return session

    def logout(self, token: str) -> bool:
        """Revokes session token."""
        if token in self.data_store.get("active_sessions", {}):
            del self.data_store["active_sessions"][token]
            return True
        return False

    def list_users(self) -> List[Dict[str, Any]]:
        """Returns safe user objects without password hashes."""
        users = []
        for u in self.data_store.get("users", []):
            users.append({
                "id": u.get("id"),
                "username": u.get("username"),
                "name": u.get("name"),
                "role": u.get("role"),
                "phone": u.get("phone", ""),
                "is_admin": u.get("is_admin", False),
                "avatar_color": u.get("avatar_color", "#3b82f6")
            })
        return users

    def register_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new employee login."""
        username = data.get("username", "").strip().lower()
        if not username:
            raise ValueError("Username is required")
            
        for u in self.data_store.get("users", []):
            if u.get("username", "").lower() == username:
                raise ValueError(f"Username '{username}' already exists")
                
        user_id = f"USR-{len(self.data_store['users']) + 1:03d}"
        password = data.get("password", "shoot2026")
        
        user_record = {
            "id": user_id,
            "username": username,
            "password_hash": self._hash_password(password),
            "name": data.get("name", username.capitalize()),
            "role": data.get("role", "Crew Member"),
            "phone": data.get("phone", ""),
            "is_admin": bool(data.get("is_admin", False)),
            "avatar_color": data.get("avatar_color", "#6366f1")
        }
        self.data_store["users"].append(user_record)
        return {
            "id": user_record["id"],
            "username": user_record["username"],
            "name": user_record["name"],
            "role": user_record["role"],
            "phone": user_record["phone"],
            "is_admin": user_record["is_admin"],
            "avatar_color": user_record["avatar_color"]
        }
