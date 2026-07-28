"""
Forsake Database — local SQLite for tracking deployment and user sessions.
Created by ANONYMOUS-BETA
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

from . import config as cfg
from .utils import hash_password, verify_password, timestamp


class ForsakeDB:
    """Local database for Forsake deployment management."""

    def __init__(self):
        cfg.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = cfg.DB_PATH
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                created_at TEXT NOT NULL,
                last_login TEXT
            );
            
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                config_json TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gophish_id INTEGER,
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                stats_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS landing_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_url TEXT,
                path TEXT NOT NULL,
                html_files INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    # ─── Users ────────────────────────────────────────────────────────────

    def create_user(self, username: str, password: str, role: str = "admin") -> int:
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, hash_password(password), role, timestamp())
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"User '{username}' already exists")
        finally:
            conn.close()

    def authenticate(self, username: str, password: str) -> Optional[int]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if row and verify_password(password, row["password_hash"]):
            # Update last login
            conn = self._get_conn()
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?",
                         (timestamp(), row["id"]))
            conn.commit()
            conn.close()
            return row["id"]
        return None

    def create_session(self, user_id: int, token: str, expires_hours: int = 8) -> str:
        from datetime import timedelta
        expires = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO sessions (user_id, token, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (user_id, token, timestamp(), expires)
        )
        conn.commit()
        conn.close()
        return token

    def validate_session(self, token: str) -> Optional[int]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT user_id, expires_at FROM sessions WHERE token = ?", (token,)
        ).fetchone()
        conn.close()
        if row:
            expires = datetime.fromisoformat(row["expires_at"])
            if datetime.now() < expires:
                return row["user_id"]
        return None

    def delete_session(self, token: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()

    # ─── Deployments ──────────────────────────────────────────────────────

    def save_deployment(self, domain: str, config: dict):
        conn = self._get_conn()
        now = timestamp()
        conn.execute(
            """INSERT INTO deployments (domain, config_json, status, created_at, updated_at)
               VALUES (?, ?, 'active', ?, ?)
               ON CONFLICT(domain) DO UPDATE SET
               config_json = excluded.config_json,
               updated_at = excluded.updated_at""",
            (domain, json.dumps(config), now, now)
        )
        conn.commit()
        conn.close()

    def get_deployments(self) -> List[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM deployments ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_deployment(self, domain: str) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM deployments WHERE domain = ?", (domain,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_deployment(self, domain: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM deployments WHERE domain = ?", (domain,))
        conn.commit()
        conn.close()

    # ─── Audit Log ────────────────────────────────────────────────────────

    def log_action(self, user_id: int, action: str, details: str = None,
                   ip_address: str = None):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO audit_log (user_id, action, details, ip_address, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, details, ip_address, timestamp())
        )
        conn.commit()
        conn.close()

    def get_audit_log(self, limit: int = 100) -> List[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
