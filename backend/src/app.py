import os
import time
import structlog
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sock import Sock
from dotenv import load_dotenv
from auth_endpoints import auth_bp
from auth import verify_jwt
from logging_config import setup_logging
from ws_handlers import register_ws_handlers

load_dotenv()

setup_logging()
logger = structlog.get_logger()

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# Registra os blueprints
app.register_blueprint(auth_bp)

# Configurar timeouts do ambiente
EXEC_TIMEOUT_S = int(os.getenv('EXEC_TIMEOUT_S', '10'))
COMPILE_TIMEOUT_S = int(os.getenv('COMPILE_TIMEOUT_S', '15'))
MAX_CODE_KB = int(os.getenv('MAX_CODE_KB', '64'))

# Registra WebSocket handlers
register_ws_handlers(app, sock, EXEC_TIMEOUT_S, COMPILE_TIMEOUT_S)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint retorna status público do backend.
    """
    return jsonify({
        "status": "ok",
    }), 200


# ============================================================================
# LIMITS ENDPOINT
# ============================================================================

@app.route('/api/limits', methods=['GET'])
def get_limits():
    """
    Get execution and compilation limits configured on backend.
    """
    return jsonify({
        "exec_timeout_s": EXEC_TIMEOUT_S,
        "compile_timeout_s": COMPILE_TIMEOUT_S,
        "max_code_kb": MAX_CODE_KB,
    }), 200


# ============================================================================
# HELLO ENDPOINT (test)
# ============================================================================

@app.route('/api/hello', methods=['GET'])
def hello():
    """Test endpoint."""
    return jsonify({"message": "Hello from Simples Editor Backend!"}), 200


# ============================================================================
# PROTECTED TEST ENDPOINT
# ============================================================================

@app.route('/api/protected', methods=['GET'])
@verify_jwt
def protected_endpoint():
    """
    Endpoint protegido que requer JWT válido.
    Demonstra uso do decorator @verify_jwt.
    """
    return jsonify({
        "message": "Acesso autorizado!",
        "user_id": request.user_id,
        "user_email": request.user_email,
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """404 Not Found handler."""
    logger.error(
        "not_found",
        error="Endpoint not found",
        status=404,
        path=request.path
    )
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """500 Internal Server Error handler."""
    logger.error(
        "internal_error",
        error=str(e),
        status=500,
        path=request.path
    )
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.before_request
def before_request():
    """Initialize request context and timing."""
    # Clear any previous context
    structlog.contextvars.clear_contextvars()
    
    # Set request start time for latency calculation
    request.start_time = time.time()
    
    # Extract user_id from request attributes (set by @verify_jwt decorator)
    user_id = getattr(request, 'user_id', None)
    
    # Bind user_id to thread-local context if available
    if user_id:
        structlog.contextvars.bind_contextvars(user_id=user_id)
    else:
        structlog.contextvars.bind_contextvars(user_id="anonymous")


@app.after_request
def after_request(response):
    """Log request completion with structured data."""
    # Calculate request latency
    latency_ms = 0.0
    if hasattr(request, 'start_time'):
        latency_ms = (time.time() - request.start_time) * 1000
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Log request with structured data: timestamp, user_id, event, status, latency_ms
    logger.info(
        "http_request",
        method=request.method,
        path=request.path,
        status=response.status_code,
        latency_ms=round(latency_ms, 2),
        content_length=response.content_length or 0
    )
    
    return response


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG', '1') == '1'
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode,
        use_reloader=True
    )
