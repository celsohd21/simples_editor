"""
Endpoints de autenticação: signup, login, logout.
Incluem logging estruturado em JSON.
"""
import uuid
import structlog
from flask import Blueprint, request, jsonify
from auth import generate_jwt_token, AuthError

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = structlog.get_logger()


# ============================================================================
# SIGNUP ENDPOINT
# ============================================================================

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Endpoint para registrar novo usuário.
    
    Body JSON:
    {
        "email": "user@example.com",
        "password": "senha123"
    }
    
    Response:
    {
        "user_id": "uuid",
        "email": "user@example.com",
        "token": "jwt_token",
        "expires_in": 86400
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            logger.warning(
                "signup_failed",
                error="Body JSON não fornecido",
                status=400
            )
            return jsonify({"error": "Body JSON não fornecido"}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # Validações
        if not email:
            logger.warning(
                "signup_failed",
                error="Email é obrigatório",
                status=400
            )
            return jsonify({"error": "Email é obrigatório"}), 400
        
        if not password:
            logger.warning(
                "signup_failed",
                error="Senha é obrigatória",
                status=400
            )
            return jsonify({"error": "Senha é obrigatória"}), 400
        
        if len(password) < 6:
            logger.warning(
                "signup_failed",
                error="Senha deve ter no mínimo 6 caracteres",
                status=400
            )
            return jsonify({"error": "Senha deve ter no mínimo 6 caracteres"}), 400
        
        if '@' not in email:
            logger.warning(
                "signup_failed",
                error="Email inválido",
                status=400
            )
            return jsonify({"error": "Email inválido"}), 400
        
        # TODO: Verificar se email já existe no banco
        # TODO: Hash da senha e salvar no banco
        # Para agora, vamos simular o comportamento
        
        # Gera um ID único para o usuário
        user_id = str(uuid.uuid4())
        
        # Gera o JWT token
        token = generate_jwt_token(user_id, email)
        
        # Log signup success
        logger.info(
            "signup_success",
            user_id=user_id,
            email=email,
            status=201
        )
        
        return jsonify({
            "user_id": user_id,
            "email": email,
            "token": token,
            "expires_in": 86400,  # 24 horas em segundos
        }), 201
    
    except Exception as e:
        logger.error(
            "signup_error",
            error=str(e),
            status=500
        )
        return jsonify({"error": f"Erro ao registrar: {str(e)}"}), 500


# ============================================================================
# LOGIN ENDPOINT
# ============================================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint para fazer login.
    
    Body JSON:
    {
        "email": "user@example.com",
        "password": "senha123"
    }
    
    Response:
    {
        "user_id": "uuid",
        "email": "user@example.com",
        "token": "jwt_token",
        "expires_in": 86400
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            logger.warning(
                "login_failed",
                error="Body JSON não fornecido",
                status=400
            )
            return jsonify({"error": "Body JSON não fornecido"}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # Validações
        if not email or not password:
            logger.warning(
                "login_failed",
                email=email,
                error="Email e senha são obrigatórios",
                status=400
            )
            return jsonify({"error": "Email e senha são obrigatórios"}), 400
        
        # TODO: Buscar usuário no banco
        # TODO: Validar password com hash
        # Para agora, vamos simular o comportamento
        
        # Simula um usuário encontrado
        user_id = str(uuid.uuid4())
        
        # Gera o JWT token
        token = generate_jwt_token(user_id, email)
        
        # Log login success
        logger.info(
            "login_success",
            user_id=user_id,
            email=email,
            status=200
        )
        
        return jsonify({
            "user_id": user_id,
            "email": email,
            "token": token,
            "expires_in": 86400,  # 24 horas em segundos
        }), 200
    
    except Exception as e:
        logger.error(
            "login_error",
            email=data.get('email', 'unknown') if data else 'unknown',
            error=str(e),
            status=500
        )
        return jsonify({"error": f"Erro ao fazer login: {str(e)}"}), 500


# ============================================================================
# LOGOUT ENDPOINT
# ============================================================================

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Endpoint para fazer logout (invalida o token no cliente).
    
    Note: O token é stateless, então o logout é apenas no cliente.
    O servidor pode manter uma blacklist de tokens se necessário (Sprint 5).
    
    Response:
    {
        "message": "Logout realizado com sucesso"
    }
    """
    logger.info(
        "logout",
        status=200
    )
    return jsonify({
        "message": "Logout realizado com sucesso"
    }), 200


# ============================================================================
# VERIFY TOKEN ENDPOINT
# ============================================================================

@auth_bp.route('/verify', methods=['POST'])
def verify():
    """
    Endpoint para verificar se um token é válido.
    
    Headers:
    Authorization: Bearer <token>
    
    Response:
    {
        "valid": true,
        "user_id": "uuid",
        "email": "user@example.com"
    }
    """
    try:
        token = None
        
        # Tenta extrair o token do header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # "Bearer <token>"
            except IndexError:
                logger.warning(
                    "verify_failed",
                    error="Formato de Authorization inválido",
                    status=401
                )
                return jsonify({"error": "Formato de Authorization inválido"}), 401
        
        if not token:
            logger.warning(
                "verify_failed",
                error="Token não fornecido",
                status=401
            )
            return jsonify({"valid": False, "error": "Token não fornecido"}), 401
        
        import jwt
        import os
        
        secret = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-min-64-chars')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        user_id = payload.get('sub')
        logger.info(
            "verify_success",
            user_id=user_id,
            status=200
        )
        
        return jsonify({
            "valid": True,
            "user_id": user_id,
            "email": payload.get('email')
        }), 200
    
    except jwt.ExpiredSignatureError:
        logger.warning(
            "verify_failed",
            error="Token expirado",
            status=401
        )
        return jsonify({"valid": False, "error": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        logger.warning(
            "verify_failed",
            error="Token inválido",
            status=401
        )
        return jsonify({"valid": False, "error": "Token inválido"}), 401
    except Exception as e:
        logger.error(
            "verify_error",
            error=str(e),
            status=500
        )
        return jsonify({"valid": False, "error": f"Erro ao verificar: {str(e)}"}), 500
