import sqlite3
import threading
from ..config import Config
from ..utils.state_serializer import serialize_state, deserialize_state


def _parse_db_path(url):
    """Extract the file path from a 'sqlite:///path' URL, or return as-is."""
    if url.startswith('sqlite:///'):
        return url[len('sqlite:///'):]
    return url


class SQLiteStore:
    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._local = threading.local()
                    cls._instance._db_lock = threading.Lock()
                    cls._instance._db_path = _parse_db_path(Config.DATABASE_URL)
                    cls._instance._init_schema()
        return cls._instance

    def init_db(self, db_path):
        """Reinitialize the store with a new database path (useful for testing)."""
        with self._db_lock:
            self._local = threading.local()
            self._db_path = db_path
            self._init_schema()

    def _get_conn(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
        return self._local.conn

    def _init_schema(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS games (
                game_id TEXT PRIMARY KEY,
                serialized_state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        )
        conn.commit()
        conn.close()

    def save(self, game_id, game_state):
        json_state = serialize_state(game_state)
        conn = self._get_conn()
        conn.execute(
            'INSERT OR REPLACE INTO games (game_id, serialized_state) VALUES (?, ?)',
            (game_id, json_state),
        )
        conn.commit()

    def load(self, game_id):
        conn = self._get_conn()
        cursor = conn.execute(
            'SELECT serialized_state FROM games WHERE game_id = ?',
            (game_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return deserialize_state(row[0])

    def delete(self, game_id):
        conn = self._get_conn()
        cursor = conn.execute(
            'DELETE FROM games WHERE game_id = ?',
            (game_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

    def exists(self, game_id):
        conn = self._get_conn()
        cursor = conn.execute(
            'SELECT 1 FROM games WHERE game_id = ?',
            (game_id,),
        )
        return cursor.fetchone() is not None

    def clear(self):
        conn = self._get_conn()
        conn.execute('DELETE FROM games')
        conn.commit()

