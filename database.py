import sqlite3
from contextlib import contextmanager
from config import Config

class Database:
    """Database manager for sessions and settings"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    rate_limit_remaining INTEGER,
                    rate_limit_reset TIMESTAMP
                )
            ''')
            
            # API Endpoints table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    base_url TEXT NOT NULL,
                    endpoints TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Session usage statistics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    endpoint TEXT,
                    response_time REAL,
                    status_code INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            ''')
            
            # Insert default API endpoints if not exists
            cursor.execute('SELECT COUNT(*) FROM api_endpoints')
            if cursor.fetchone()[0] == 0:
                import json
                cursor.execute('''
                    INSERT INTO api_endpoints (name, base_url, endpoints, is_default)
                    VALUES (?, ?, ?, ?)
                ''', (
                    'WorldQuant Brain Production',
                    Config.DEFAULT_ENDPOINTS['base_url'],
                    json.dumps({k: v for k, v in Config.DEFAULT_ENDPOINTS.items() 
                               if k != 'base_url'}),
                    1
                ))