import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from auth_endpoints import auth_bp
from auth import verify_jwt

load_dotenv()

app = Flask(__name__)
CORS(app)

# Registra os blueprints
app.register_blueprint(auth_bp)

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
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """500 Internal Server Error handler."""
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.before_request
def before_request():
    """Log incoming requests."""
    pass


@app.after_request
def after_request(response):
    """Add security headers."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
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
