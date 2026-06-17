import json
import sqlite3
from datetime import datetime

class APIEndpointManager:
    """Manages dynamic API endpoints"""
    
    def __init__(self, database):
        self.db = database
    
    def get_all_endpoints(self) -> list:
        """Get all configured API endpoints"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM api_endpoints ORDER BY is_default DESC, name')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_default_endpoint(self) -> dict:
        """Get default API endpoint configuration"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM api_endpoints WHERE is_default = 1 LIMIT 1')
            row = cursor.fetchone()
            if row:
                return dict(row)
            # Return default if none configured
            from ..config import Config
            return {
                'name': 'Default',
                'base_url': Config.DEFAULT_ENDPOINTS['base_url'],
                'endpoints': json.dumps({k: v for k, v in Config.DEFAULT_ENDPOINTS.items() 
                                        if k != 'base_url'})
            }
    
    def add_endpoint(self, name: str, base_url: str, endpoints: dict, 
                     is_default: bool = False) -> dict:
        """Add new API endpoint configuration"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if is_default:
                cursor.execute('UPDATE api_endpoints SET is_default = 0')
            
            try:
                cursor.execute('''
                    INSERT INTO api_endpoints (name, base_url, endpoints, is_default)
                    VALUES (?, ?, ?, ?)
                ''', (name, base_url, json.dumps(endpoints), is_default))
                return {'success': True, 'id': cursor.lastrowid}
            except sqlite3.IntegrityError:
                return {'success': False, 'error': 'Endpoint name already exists'}
    
    def update_endpoint(self, endpoint_id: int, name: str, base_url: str,
                       endpoints: dict, is_default: bool = False) -> bool:
        """Update API endpoint configuration"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if is_default:
                cursor.execute('UPDATE api_endpoints SET is_default = 0')
            
            cursor.execute('''
                UPDATE api_endpoints
                SET name = ?, base_url = ?, endpoints = ?, is_default = ?
                WHERE id = ?
            ''', (name, base_url, json.dumps(endpoints), is_default, endpoint_id))
            
            return cursor.rowcount > 0
    
    def delete_endpoint(self, endpoint_id: int) -> bool:
        """Delete API endpoint (cannot delete default)"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT is_default FROM api_endpoints WHERE id = ?', 
                          (endpoint_id,))
            row = cursor.fetchone()
            if row and row['is_default']:
                return False  # Cannot delete default
            cursor.execute('DELETE FROM api_endpoints WHERE id = ?', (endpoint_id,))
            return cursor.rowcount > 0
    
    def set_default(self, endpoint_id: int) -> bool:
        """Set an endpoint as default"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE api_endpoints SET is_default = 0')
            cursor.execute('''
                UPDATE api_endpoints SET is_default = 1 WHERE id = ?
            ''', (endpoint_id,))
            return cursor.rowcount > 0
    
    def get_endpoint_url(self, endpoint_name: str, endpoint_id: int = None) -> str:
        """Get full URL for an endpoint"""
        if endpoint_id:
            config = self.get_endpoint_by_id(endpoint_id)
        else:
            config = self.get_default_endpoint()

        endpoints = json.loads(config['endpoints'])
        base_url = config['base_url'].rstrip('/')
        path = endpoints.get(endpoint_name, f'/{endpoint_name}')
        if not path.startswith('/'):
            path = f'/{path}'

        return f"{base_url}{path}"
    
    def get_endpoint_by_id(self, endpoint_id: int) -> dict:
        """Get endpoint by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM api_endpoints WHERE id = ?', (endpoint_id,))
            row = cursor.fetchone()
            return dict(row) if row else None