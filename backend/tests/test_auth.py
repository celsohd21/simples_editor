"""
Testes para endpoints de autenticação.
"""
import pytest
import json
import sys
import os

# Adiciona o diretório src ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app


@pytest.fixture
def client():
    """Fixture que retorna um cliente de teste do Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAuthEndpoints:
    """Testes para endpoints de autenticação."""

    def test_health_check(self, client):
        """Testa endpoint de health check."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'

    def test_signup_success(self, client):
        """Testa signup bem-sucedido."""
        payload = {
            "email": "teste@example.com",
            "password": "senha123"
        }
        response = client.post(
            '/api/auth/signup',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'user_id' in data
        assert 'token' in data
        assert 'expires_in' in data
        assert data['email'] == 'teste@example.com'
        assert data['expires_in'] == 86400

    def test_signup_missing_email(self, client):
        """Testa signup sem email."""
        payload = {
            "password": "senha123"
        }
        response = client.post(
            '/api/auth/signup',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_signup_missing_password(self, client):
        """Testa signup sem senha."""
        payload = {
            "email": "teste@example.com"
        }
        response = client.post(
            '/api/auth/signup',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_signup_short_password(self, client):
        """Testa signup com senha muito curta."""
        payload = {
            "email": "teste@example.com",
            "password": "123"
        }
        response = client.post(
            '/api/auth/signup',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert '6' in data['error']  # Mensagem deve mencionar 6 caracteres

    def test_signup_invalid_email(self, client):
        """Testa signup com email inválido."""
        payload = {
            "email": "nao-eh-um-email",
            "password": "senha123"
        }
        response = client.post(
            '/api/auth/signup',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_login_success(self, client):
        """Testa login bem-sucedido."""
        payload = {
            "email": "teste@example.com",
            "password": "senha123"
        }
        response = client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'user_id' in data
        assert 'token' in data
        assert 'expires_in' in data
        assert data['email'] == 'teste@example.com'

    def test_login_missing_credentials(self, client):
        """Testa login sem credenciais."""
        payload = {}
        response = client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_logout(self, client):
        """Testa logout."""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data

    def test_verify_token_valid(self, client):
        """Testa verificação de token válido."""
        # Primeiro faz signup para obter um token
        signup_payload = {
            "email": "teste@example.com",
            "password": "senha123"
        }
        signup_response = client.post(
            '/api/auth/signup',
            data=json.dumps(signup_payload),
            content_type='application/json'
        )
        signup_data = json.loads(signup_response.data)
        token = signup_data['token']
        
        # Agora verifica o token
        headers = {
            'Authorization': f'Bearer {token}'
        }
        response = client.post('/api/auth/verify', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] is True
        assert 'user_id' in data
        assert 'email' in data

    def test_verify_token_missing(self, client):
        """Testa verificação sem token."""
        response = client.post('/api/auth/verify')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['valid'] is False

    def test_protected_endpoint_with_token(self, client):
        """Testa acesso a endpoint protegido com token válido."""
        # Primeiro faz signup para obter um token
        signup_payload = {
            "email": "teste@example.com",
            "password": "senha123"
        }
        signup_response = client.post(
            '/api/auth/signup',
            data=json.dumps(signup_payload),
            content_type='application/json'
        )
        signup_data = json.loads(signup_response.data)
        token = signup_data['token']
        
        # Acessa o endpoint protegido
        headers = {
            'Authorization': f'Bearer {token}'
        }
        response = client.get('/api/protected', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert data['message'] == 'Acesso autorizado!'
        assert 'user_id' in data
        assert 'user_email' in data

    def test_protected_endpoint_without_token(self, client):
        """Testa acesso a endpoint protegido sem token."""
        response = client.get('/api/protected')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_protected_endpoint_invalid_token(self, client):
        """Testa acesso a endpoint protegido com token inválido."""
        headers = {
            'Authorization': 'Bearer token_invalido_xyz'
        }
        response = client.get('/api/protected', headers=headers)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
