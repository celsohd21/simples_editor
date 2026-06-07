# Autenticação - Simples Editor

## Visão Geral

O Simples Editor utiliza **Supabase Auth** para autenticação com email/senha e **JWT tokens** para autorização nos endpoints protegidos.

## Configuração

### Variáveis de Ambiente

Configure as seguintes variáveis no arquivo `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SECRET_KEY=your-secret-key-min-64-chars
```

Use `.env.example` como referência.

## Endpoints de Autenticação

### 1. Signup (Registrar novo usuário)

**POST** `/api/auth/signup`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (201):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}
```

**Validações:**
- Email é obrigatório e deve ser válido
- Senha é obrigatória e deve ter mínimo 6 caracteres

### 2. Login (Autenticar usuário)

**POST** `/api/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}
```

### 3. Logout (Encerrar sessão)

**POST** `/api/auth/logout`

**Response (200):**
```json
{
  "message": "Logout realizado com sucesso"
}
```

**Nota:** Como os tokens são stateless, o logout é apenas no cliente (remover token do localStorage).

### 4. Verify Token (Verificar validade do token)

**POST** `/api/auth/verify`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "valid": true,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

**Response (401):**
```json
{
  "valid": false,
  "error": "Token expirado"
}
```

## Usando JWT em Endpoints Protegidos

### Decorator @verify_jwt

Para proteger um endpoint, use o decorator `@verify_jwt`:

```python
from flask import request, jsonify
from auth import verify_jwt

@app.route('/api/protected')
@verify_jwt
def protected_endpoint():
    user_id = request.user_id
    user_email = request.user_email
    return jsonify({
        "message": "Acesso autorizado!",
        "user_id": user_id,
        "user_email": user_email
    }), 200
```

O decorator:
1. Extrai o token do header `Authorization: Bearer <token>`
2. Valida a assinatura do token
3. Verifica se o token não expirou
4. Adiciona `request.user_id` e `request.user_email` ao objeto request

### Requisições para Endpoints Protegidos

**Headers:**
```
Authorization: Bearer <token>
```

**Exemplo (curl):**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:5000/api/protected
```

## JWT Token Structure

Um JWT token contém os seguintes claims:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "email": "user@example.com",
  "iat": 1654321200,                               // issued at
  "exp": 1654407600,                               // expires at (24h após emissão)
  "iss": "simples-editor"                          // issuer
}
```

## Segurança

⚠️ **Importante:**

1. **Nunca commite o arquivo `.env`** com credenciais reais
2. **Use HTTPS em produção** para transmitir tokens
3. **Nunca armazene senhas em plain text** (implementar hash bcrypt na Sprint 2)
4. **Mantenha `SECRET_KEY` segura** e com pelo menos 64 caracteres em produção
5. **Tokens são stateless**: logout apenas remove o token no cliente (implementar blacklist em Sprint 5 se necessário)

## Testes

Execute os testes de autenticação:

```bash
cd backend
pytest tests/test_auth.py -v
```

Exemplo de resultado:
```
tests/test_auth.py::TestAuthEndpoints::test_signup_success PASSED
tests/test_auth.py::TestAuthEndpoints::test_login_success PASSED
tests/test_auth.py::TestAuthEndpoints::test_protected_endpoint_with_token PASSED
tests/test_auth.py::TestAuthEndpoints::test_verify_token_valid PASSED
```

## Próximos Passos

- **Sprint 2:** Integrar com banco de dados (usuários, hash bcrypt)
- **Sprint 2:** Implementar refresh tokens
- **Sprint 5:** Adicionar token blacklist para logout real
- **Sprint 5:** Rate limiting de login por IP/email
