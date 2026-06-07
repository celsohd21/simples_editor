"""
Autenticação e autorização com Supabase e JWT.
"""
import os
import jwt
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, current_app


# ============================================================================
# SUPABASE AUTH SERVICE
# ============================================================================

class SupabaseAuth:
    """Service para comunicação com Supabase Auth."""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar definidas no .env")

    def get_jwt_secret(self):
        """
        Retorna a chave para verificar JWT do Supabase.
        Em produção, isso viria de um endpoint específico do Supabase.
        """
        # O Supabase usa a ANON_KEY para assinar tokens
        # A chave é: ANON_KEY[:36] (primeira 36 chars) + SECRET_KEY
        return os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-min-64-chars')


supabase_auth = SupabaseAuth()


# ============================================================================
# JWT VERIFICATION DECORATOR
# ============================================================================

def verify_jwt(f):
    """
    Decorator para verificar JWT tokens em endpoints protegidos.
    
    Uso:
        @app.route('/api/protected')
        @verify_jwt
        def protected_endpoint():
            user_id = request.user_id
            return jsonify({"user_id": user_id})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Tenta extrair o token do header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # "Bearer <token>"
            except IndexError:
                return jsonify({"error": "Formato de Authorization inválido"}), 401
        
        if not token:
            return jsonify({"error": "Token não fornecido"}), 401
        
        try:
            # Decodifica e valida o token
            secret = supabase_auth.get_jwt_secret()
            payload = jwt.decode(
                token,
                secret,
                algorithms=['HS256']
            )
            
            # Adiciona o payload ao request para uso posterior
            request.user_id = payload.get('sub')  # subject (user_id)
            request.user_email = payload.get('email')
            request.token_payload = payload
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": f"Token inválido: {str(e)}"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================================================
# JWT GENERATION
# ============================================================================

def generate_jwt_token(user_id: str, email: str, expires_in_hours: int = 24) -> str:
    """
    Gera um JWT token com claims básicos.
    
    Args:
        user_id: ID único do usuário
        email: Email do usuário
        expires_in_hours: Tempo de expiração em horas
    
    Returns:
        Token JWT como string
    """
    secret = supabase_auth.get_jwt_secret()
    now = datetime.utcnow()
    expire = now + timedelta(hours=expires_in_hours)
    
    payload = {
        'sub': user_id,  # subject (user_id)
        'email': email,
        'iat': now,
        'exp': expire,
        'iss': 'simples-editor',  # issuer
    }
    
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token


# ============================================================================
# ERROR RESPONSES
# ============================================================================

class AuthError(Exception):
    """Exceção customizada para erros de autenticação."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
