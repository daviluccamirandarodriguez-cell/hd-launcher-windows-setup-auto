"""Local accounts and per-user game library for HD Launcher.

No internet connection, no payment system, no credential syncing.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3
import uuid


CATALOG = (
    {
        "id": "neon-dodge",
        "title": "Neon Dodge",
        "genre": "Arcade",
        "description": "Desvie dos obstáculos e sobreviva o máximo possível.",
        "color": "#00D769",
        "symbol": "ND",
    },
    {
        "id": "star-catcher",
        "title": "Caça-Estrelas",
        "genre": "Casual",
        "description": "Pegue estrelas amarelas, evite bombas azuis e faça pontos.",
        "color": "#FFD600",
        "symbol": "★",
    },
    {
        "id": "reflex-rush",
        "title": "Reflexo Turbo",
        "genre": "Reflexos",
        "description": "Clique nos alvos antes que o tempo acabe.",
        "color": "#398BFF",
        "symbol": "RT",
    },
    {
        "id": "the-cars-hd",
        "title": "The Cars HD",
        "genre": "Corrida",
        "description": "Corrida urbana arcade com 3 carros, nitro, itens e rivais. Protótipo 2.5D.",
        "color": "#38ADFF",
        "symbol": "HD",
    },
)
CATALOG_BY_ID = {game["id"]: game for game in CATALOG}


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)


class Storage:
    def __init__(self, root: Path | None = None):
        if root is None:
            roaming = os.environ.get("APPDATA")
            root = Path(roaming) / "HDLauncher" if roaming else Path.home() / ".hd_launcher"
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "accounts.db"
        self._create_tables()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.database)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _create_tables(self):
        with self.connect() as conn:
            # Keep the v1.2 names and columns, so existing accounts still work.
            conn.execute("""CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                salt BLOB NOT NULL,
                password_hash BLOB NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                path TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id,path)
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS free_installs (
                user_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                installed_at TEXT NOT NULL,
                PRIMARY KEY (user_id,game_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )""")

    @staticmethod
    def validate_credentials(username: str, password: str):
        if not (3 <= len(username) <= 32) or not username.replace("_", "").isalnum():
            raise ValueError("O usuário precisa ter de 3 a 32 letras, números ou _. ")
        if len(password) < 8:
            raise ValueError("A senha precisa ter pelo menos 8 caracteres.")

    def register(self, username: str, password: str) -> tuple[str, str]:
        username = username.strip()
        self.validate_credentials(username, password)
        salt = secrets.token_bytes(16)
        user_id = uuid.uuid4().hex
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO users (id,username,salt,password_hash) VALUES (?,?,?,?)",
                    (user_id, username, salt, _hash_password(password, salt)),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Este nome de usuário já está em uso.") from exc
        return user_id, username

    def login(self, username: str, password: str) -> tuple[str, str] | None:
        username = username.strip()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id,username,salt,password_hash FROM users WHERE username=?", (username,)
            ).fetchone()
        if row is None:
            return None
        if not hmac.compare_digest(_hash_password(password, row[2]), row[3]):
            return None
        return row[0], row[1]

    def installed_ids(self, user_id: str) -> set[str]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT game_id FROM free_installs WHERE user_id=?", (user_id,)
            ).fetchall()
        return {row[0] for row in rows if row[0] in CATALOG_BY_ID}

    def install_free_game(self, user_id: str, game_id: str):
        if game_id not in CATALOG_BY_ID:
            raise ValueError("Este jogo não está na loja.")
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO free_installs (user_id,game_id,installed_at) VALUES (?,?,?)",
                (user_id, game_id, datetime.now(timezone.utc).isoformat()),
            )

    def uninstall_free_game(self, user_id: str, game_id: str):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM free_installs WHERE user_id=? AND game_id=?", (user_id, game_id)
            )

    def local_games(self, user_id: str) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id,title,path FROM games WHERE user_id=? ORDER BY title COLLATE NOCASE", (user_id,)
            ).fetchall()
        return [{"id": row[0], "title": row[1], "path": row[2]} for row in rows]

    def add_local_game(self, user_id: str, path: str) -> bool:
        path = str(Path(path).resolve())
        if Path(path).suffix.lower() != ".exe" or not Path(path).is_file():
            raise ValueError("Selecione um arquivo .exe existente.")
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO games (id,user_id,title,path) VALUES (?,?,?,?)",
                    (uuid.uuid4().hex, user_id, Path(path).stem, path),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def remove_local_game(self, user_id: str, game_id: str):
        with self.connect() as conn:
            conn.execute("DELETE FROM games WHERE user_id=? AND id=?", (user_id, game_id))
