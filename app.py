from flask import Flask, render_template, request, jsonify, session
from models.session_manager import SessionManager
from models.api_endpoint_manager import APIEndpointManager
from models.operator_formatter import OperatorFormatter
from models.dataset_formatter import DatasetFormatter
from database import Database
from config import Config
import json
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize components

db = Database()
session_manager = SessionManager(db)
endpoint_manager = APIEndpointManager(db)
operator_formatter = OperatorFormatter()
dataset_formatter = DatasetFormatter()

@app.route('/')
def index():
    return jsonify({"status": "Backend is running", "frontend_url": "https://ellonding109.github.io/worldquant_frontend"})

# Session Management Routes
@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions"""
    sessions = session_manager.get_all_sessions()
    return jsonify({'success': True, 'sessions': sessions})

@app.route('/api/sessions', methods=['POST'])
def add_session():
    """Add new session"""
    data = request.json
    result = session_manager.add_session(
        name=data['name'],
        token=data['token']
    )
    return jsonify(result)

@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """Get single session"""
    sess = session_manager.get_session(session_id)
    if sess:
        return jsonify({'success': True, 'session': sess})
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.route('/api/sessions/<int:session_id>/validate', methods=['POST'])
def validate_session(session_id):
    """Validate session"""
    endpoint_config = endpoint_manager.get_default_endpoint()
    result = session_manager.validate_session(
        session_id, 
        endpoint_config['base_url']
    )
    return jsonify(result)

@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete session"""
    success = session_manager.delete_session(session_id)
    return jsonify({'success': success})

@app.route('/api/sessions/<int:session_id>/stats', methods=['GET'])
def get_session_stats(session_id):
    """Get session statistics"""
    days = request.args.get('days', 7, type=int)
    stats = session_manager.get_session_stats(session_id, days)
    return jsonify({'success': True, 'stats': stats})

# API Endpoint Management Routes
@app.route('/api/endpoints', methods=['GET'])
def get_endpoints():
    """Get all API endpoints"""
    endpoints = endpoint_manager.get_all_endpoints()
    return jsonify({'success': True, 'endpoints': endpoints})

@app.route('/api/endpoints/default', methods=['GET'])
def get_default_endpoint():
    """Get default endpoint"""
    endpoint = endpoint_manager.get_default_endpoint()
    return jsonify({'success': True, 'endpoint': endpoint})

@app.route('/api/endpoints', methods=['POST'])
def add_endpoint():
    """Add new endpoint"""
    data = request.json
    result = endpoint_manager.add_endpoint(
        name=data['name'],
        base_url=data['base_url'],
        endpoints=data['endpoints'],
        is_default=data.get('is_default', False)
    )
    return jsonify(result)

@app.route('/api/endpoints/<int:endpoint_id>', methods=['PUT'])
def update_endpoint(endpoint_id):
    """Update endpoint"""
    data = request.json
    success = endpoint_manager.update_endpoint(
        endpoint_id=endpoint_id,
        name=data['name'],
        base_url=data['base_url'],
        endpoints=data['endpoints'],
        is_default=data.get('is_default', False)
    )
    return jsonify({'success': success})

@app.route('/api/endpoints/<int:endpoint_id>/default', methods=['POST'])
def set_default_endpoint(endpoint_id):
    """Set endpoint as default"""
    success = endpoint_manager.set_default(endpoint_id)
    return jsonify({'success': success})

@app.route('/api/endpoints/<int:endpoint_id>', methods=['DELETE'])
def delete_endpoint(endpoint_id):
    """Delete endpoint"""
    success = endpoint_manager.delete_endpoint(endpoint_id)
    return jsonify({'success': success})

# Operators Routes
@app.route('/api/operators', methods=['GET'])
def get_operators():
    """Fetch and format operators"""
    session_id = request.args.get('session_id', type=int)
    format_type = request.args.get('format', 'compact')
    categories = request.args.getlist('categories')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'Session ID required'}), 400
    
    try:
        brain_session = session_manager.create_requests_session(session_id)
        endpoint_url = endpoint_manager.get_endpoint_url('operators')
        
        response = brain_session.get(endpoint_url, timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()
        operators = response.json()
        
        formatted = operator_formatter.format(
            operators, 
            format_type=format_type,
            categories=categories if categories else None
        )
        
        stats = operator_formatter.get_statistics(operators)
        
        return jsonify({
            'success': True,
            'operators': formatted,
            'statistics': stats,
            'count': len(operators)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/operators/categories', methods=['GET'])
def get_operator_categories():
    """Get available operator categories"""
    session_id = request.args.get('session_id', type=int)
    
    if not session_id:
        return jsonify({'success': False, 'error': 'Session ID required'}), 400
    
    try:
        brain_session = session_manager.create_requests_session(session_id)
        endpoint_url = endpoint_manager.get_endpoint_url('operators')
        
        response = brain_session.get(endpoint_url, timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()
        operators = response.json()
        
        categories = list(set(op.get('category', 'Other') for op in operators))
        
        return jsonify({
            'success': True,
            'categories': sorted(categories)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Data Sets Routes
@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    """Fetch datasets"""
    session_id = request.args.get('session_id', type=int)
    
    if not session_id:
        return jsonify({'success': False, 'error': 'Session ID required'}), 400
    
    try:
        brain_session = session_manager.create_requests_session(session_id)
        endpoint_url = endpoint_manager.get_endpoint_url('data_sets')
        
        response = brain_session.get(endpoint_url, timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()
        
        return jsonify({
            'success': True,
            'datasets': response.json()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<path:dataset_id>/fields', methods=['GET'])
def get_dataset_fields(dataset_id):
    """Fetch dataset fields"""
    session_id = request.args.get('session_id', type=int)
    delay = request.args.get('delay', 1, type=int)
    instrument_type = request.args.get('instrument_type', 'EQUITY')
    region = request.args.get('region')
    universe = request.args.get('universe')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'Session ID required'}), 400
    if not region or not universe:
        return jsonify({'success': False, 'error': 'Region and universe required'}), 400
    
    try:
        brain_session = session_manager.create_requests_session(session_id)
        endpoint_url = endpoint_manager.get_endpoint_url('data_fields')
        params = {
            'dataset.id': dataset_id,
            'delay': delay,
            'instrumentType': instrument_type,
            'region': region,
            'universe': universe,
            'limit': 20,
            'offset': 0
        }

        response = brain_session.get(
            endpoint_url,
            params=params,
            timeout=Config.REQUEST_TIMEOUT
        )
        if response.status_code == 404:
            params.pop('dataset.id', None)
            params['dataSet'] = dataset_id
            response = brain_session.get(
                endpoint_url,
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )

        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            all_fields = data
        else:
            all_fields = data.get('results', data.get('fields', data.get('data', [])))
        count = data.get('count', len(all_fields)) if isinstance(data, dict) else len(all_fields)

        while isinstance(data, dict) and data.get('next'):
            params['offset'] += params['limit']
            response = brain_session.get(
                endpoint_url,
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            all_fields.extend(data.get('results', data.get('fields', [])))
        
        return jsonify({
            'success': True,
            'fields': all_fields,
            'count': len(all_fields)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<path:dataset_id>/details', methods=['GET'])
def get_dataset_details(dataset_id):
    """Fetch detailed dataset metadata and format it."""
    session_id = request.args.get('session_id', type=int)
    if not session_id:
        return jsonify({'success': False, 'error': 'Session ID required'}), 400

    try:
        brain_session = session_manager.create_requests_session(session_id)
        base_endpoint = endpoint_manager.get_endpoint_url('data_sets').rstrip('/')
        response = brain_session.get(
            f"{base_endpoint}/{quote(dataset_id, safe='/')}",
            timeout=Config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        dataset = response.json()
        formatted = dataset_formatter.format(dataset, format_type='markdown')
        relevant = dataset_formatter.extract_relevant(dataset)

        return jsonify({
            'success': True,
            'dataset': relevant,
            'formatted': formatted
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
