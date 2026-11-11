'''Memory management - session_id scoped window + summary memory
SQLite persistence with absolute path, survives server restarts.
'''
import os as _os
import sqlite3
import threading
from datetime import datetime, timezone, timedelta

_TZ = timezone(timedelta(hours=8))
_DB_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_DB_PATH = _os.path.join(_DB_DIR, "memory.db")

def _now():
    return datetime.now(_TZ).isoformat()

class _Storage:
    def __init__(self, db_path=None):
        self._db_path = db_path or _DB_PATH
        self._local = threading.local()
        self._init_db()

    def _get_conn(self):
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " session_id TEXT NOT NULL,"
            " role TEXT NOT NULL,"
            " content TEXT NOT NULL,"
            " created_at TEXT NOT NULL"
            ")"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")
        conn.commit()

    def add(self, session_id, role, content):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO messages (session_id,role,content,created_at) VALUES (?,?,?,?)",
            (session_id, role, content, _now()),
        )
        conn.commit()

    def get_messages(self, session_id, limit=None):
        conn = self._get_conn()
        if limit:
            rows = conn.execute(
                "SELECT role,content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
            rows = list(reversed(rows))
        else:
            rows = conn.execute(
                "SELECT role,content FROM messages WHERE session_id=? ORDER BY id",
                (session_id,),
            ).fetchall()
        return [{"role": r, "content": c} for r, c in rows]

    def delete_session(self, session_id):
        conn = self._get_conn()
        conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        conn.commit()

    def session_count(self):
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(DISTINCT session_id) FROM messages").fetchone()
        return row[0] if row else 0

_storage = _Storage()

NL = chr(10)

class WindowMemory:
    def __init__(self, session_id, k=20):
        self.session_id = session_id
        self.k = k

    def load_memory_variables(self, _inputs=None):
        msgs = _storage.get_messages(self.session_id, limit=self.k * 2)
        if not msgs:
            return {"history": ""}
        lines = [("user" if m["role"] == "user" else "assistant") + ": " + m["content"] for m in msgs]
        return {"history": NL.join(lines)}

    def save_context(self, inputs, outputs):
        _storage.add(self.session_id, "user", inputs.get("user_input", ""))
        _storage.add(self.session_id, "ai", outputs.get("output", ""))

    def clear(self):
        _storage.delete_session(self.session_id)

class SummaryMemory:
    def __init__(self, session_id):
        self.session_id = session_id
        self._summary = ""

    def load_memory_variables(self, _inputs=None):
        return {"history": "[Summary]" + NL + self._summary if self._summary else ""}

    def save_context(self, inputs, outputs):
        _storage.add(self.session_id, "user", inputs.get("user_input", ""))
        _storage.add(self.session_id, "ai", outputs.get("output", ""))

    async def summarize(self, model):
        from langchain_core.messages import SystemMessage, HumanMessage
        msgs = _storage.get_messages(self.session_id, limit=20)
        if not msgs:
            return ""
        text = NL.join(f"{m['role']}: {m['content']}" for m in msgs)
        msgs_in = [SystemMessage(content="Summarize in Chinese, under 150 chars."), HumanMessage(content=text)]
        result = await model.ainvoke(msgs_in)
        self._summary = result.content if hasattr(result, "content") else str(result)
        return self._summary

    def clear(self):
        _storage.delete_session(self.session_id)
        self._summary = ""

def get_session_memory(session_id, memory_type="window", k=20):
    session_id = session_id.strip() or "default"
    if memory_type == "summary":
        return SummaryMemory(session_id)
    return WindowMemory(session_id, k=k)

def clear_session_memory(session_id):
    _storage.delete_session(session_id)

def get_session_count():
    return _storage.session_count()
