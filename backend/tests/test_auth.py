import pytest
from flask import Flask, request, jsonify
from auth import verify_jwt, generate_jwt_token, supabase_auth
from auth_endpoints import auth_bp
from unittest.mock import patch, MagicMock

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(auth_bp)

    @app.route('/protected')
    @verify_jwt
    def protected():
        return jsonify({"user_id": request.user_id})
        
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_verify_jwt_missing_token(client):
    response = client.get('/protected')
    assert response.status_code == 401
    assert b"Token n\xc3\xa3o fornecido" in response.data or b"Token n\\u00e3o fornecido" in response.data

def test_verify_jwt_invalid_format(client):
    response = client.get('/protected', headers={"Authorization": "InvalidTokenFormat"})
    assert response.status_code == 401

@patch("auth.jwt.decode")
def test_verify_jwt_success(mock_decode, client):
    mock_decode.return_value = {"sub": "123", "email": "test@test.com"}
    response = client.get('/protected', headers={"Authorization": "Bearer dummy_token"})
    assert response.status_code == 200
    assert b"123" in response.data

def test_signup_missing_email(client):
    response = client.post('/api/auth/signup', json={"password": "pwd"})
    assert response.status_code == 400

def test_signup_success(client, mocker):
    mocker.patch("auth_endpoints.generate_jwt_token", return_value="fake_token")
    response = client.post('/api/auth/signup', json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 201
    assert b"fake_token" in response.data
