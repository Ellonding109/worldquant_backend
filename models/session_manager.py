import sqlite3
import requests
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from config import Config
import json
import base64

class SessionManager:
    """Manages API sessions with encryption and validation"""

    def __init__(self, database):
        self.db = database
        self.cipher = Fernet(base64.urlsafe_b64encode(
            Config.ENCRYPTION_KEY.encode()[:32].ljust(32, b'=')
        ))
        self.sessions = {}  # Cache active sessions

    def encrypt_token(self, token: str) -> str:
        """Encrypt session token"""
        return self.cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt session token"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()

    def add_session(self, name: str, token: str) -> dict:
        """Add a new session"""
        encrypted_token = self.encrypt_token(token)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO sessions (name, token, last_used)
                    VALUES (?, ?, ?)
                ''', (name, encrypted_token, datetime.now()))
                session_id = cursor.lastrowid
                return {'success': True, 'id': session_id, 'name': name}
            except sqlite3.IntegrityError:
                return {'success': False, 'error': 'Session name already exists'}

    def get_session(self, session_id: int) -> dict:
        """Get session by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_sessions(self) -> list:
        """Get all sessions with status"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, created_at, last_used, is_active,
                       rate_limit_remaining, rate_limit_reset
                FROM sessions
                ORDER BY last_used DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def validate_session(self, session_id: int, base_url: str) -> dict:
        """Validate session and get status"""
        session = self.get_session(session_id)
        if not session:
            return {'valid': False, 'error': 'Session not found'}

        token = self.decrypt_token(session['token'])
        test_session = requests.Session()
        test_session.cookies.set('t', token)
        test_session.headers.update({'User-Agent': 'WQBrain-Manager/1.0'})

        try:
            start_time = datetime.now()
            response = test_session.get(
                f"{base_url}/operators",
                timeout=Config.REQUEST_TIMEOUT
            )
            response_time = (datetime.now() - start_time).total_seconds()

            # Update last used
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions 
                    SET last_used = ?, is_active = 1
                    WHERE id = ?
                ''', (datetime.now(), session_id))

            # Check rate limit headers
            rate_remaining = int(response.headers.get('X-RateLimit-Remaining', 1000))
            rate_reset = response.headers.get('X-RateLimit-Reset')

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions 
                    SET rate_limit_remaining = ?, rate_limit_reset = ?
                    WHERE id = ?
                ''', (rate_remaining, rate_reset, session_id))

            status = 'active'
            if response.status_code == 429:
                status = 'rate_limited'
            elif response.status_code == 401:
                status = 'expired'
            elif response.status_code != 200:
                status = 'invalid'

            return {
                'valid': status == 'active',
                'status': status,
                'response_time': response_time,
                'rate_remaining': rate_remaining,
                'operators_count': len(response.json()) if status == 'active' else 0
            }

        except requests.exceptions.RequestException as e:
            return {'valid': False, 'error': str(e), 'status': 'error'}

    def create_requests_session(self, session_id: int) -> requests.Session:
        """Create authenticated requests session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        token = self.decrypt_token(session['token'])
        req_session = requests.Session()
        req_session.cookies.set('t', token)
        req_session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'WQBrain-Manager/1.0'
        })

        # Add retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry = Retry(
            total=Config.MAX_RETRIES,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        req_session.mount('https://', adapter)

        return req_session

    def delete_session(self, session_id: int) -> bool:
        """Delete a session"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            return cursor.rowcount > 0

    def get_session_stats(self, session_id: int, days: int = 7) -> dict:
        """Get session usage statistics"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(response_time) as avg_response_time,
                    MAX(timestamp) as last_request,
                    endpoint,
                    COUNT(*) as endpoint_count
                FROM session_stats
                WHERE session_id = ? 
                AND timestamp >= datetime('now', ?)
                GROUP BY endpoint
            ''', (session_id, f'-{days} days'))

            stats = cursor.fetchall()
            return {
                'endpoints': [dict(s) for s in stats],
                'total': sum(dict(s)['endpoint_count'] for s in stats)
            }