# 🖥️ Simples Editor — Web IDE

Uma IDE web para a linguagem **SIMPLES**, permitindo aos alunos escrever, compilar e executar programas direto no navegador sem instalação local.

---

## 🚀 Quickstart

### Pré-requisitos
- **Docker** ≥ 20.10
- **Docker Compose** ≥ 2.0

### Como rodar

```bash
# 1. Clone o repositório
git clone https://github.com/celsohd21/simples_editor.git
cd simples_editor/simples_editor

# 2. Configure as variáveis de ambiente
cp .env.example .env

# 3. Rode os containers
docker compose up --build

# 4. Acesse
Abra seu navegador em: http://localhost
```

**Tempo esperado:** 3-5 minutos para build inicial

---

## 📦 Stack Técnica

| Componente | Tecnologia | Porta |
|------------|-----------|-------|
| Frontend | React 18 + Vite + TypeScript | 5173 |
| Backend | Flask + Python 3.11 | 5000 |
| Reverse Proxy | Nginx (Alpine) | 80 |
| Auth | Supabase | — |

---

## 🏗️ Arquitetura

```
localhost:80 (Nginx)
    ├─ /api/* → Backend (Flask)
    ├─ /ws/*  → WebSocket (Backend)
    └─ /      → Frontend (React)
```

**Fluxo:**
1. Usuário acessa `http://localhost`
2. Nginx roteia para frontend (React dev server em :5173)
3. Frontend faz requests para `/api/*` → backend (:5000)
4. Backend valida JWT, processa compilação/execução

---

## 📂 Estrutura do Projeto

```
simples_editor/
├── docker/
│   ├── nginx.Dockerfile      # Nginx (reverse proxy)
│   ├── frontend.Dockerfile   # React + Vite
│   ├── backend.Dockerfile    # Flask
│   └── nginx.conf            # Configuração de rotas
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # Entry point React
│   │   ├── App.jsx           # Componente principal
│   │   └── App.css           # Estilos
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tsconfig.json
├── backend/
│   ├── src/
│   │   └── app.py            # App Flask principal
│   └── requirements.txt
├── docker-compose.yml        # Orquestração
├── .env.example              # Template de env vars
└── README.md
```

---

## 🛠️ Desenvolvimento

### Frontend
```bash
# Acessar terminal do frontend
docker compose exec frontend sh

# Dentro do container:
npm run dev      # Vite dev server (já rodando)
npm run build    # Build para produção
npm run lint     # ESLint
```

### Backend
```bash
# Acessar terminal do backend
docker compose exec backend bash

# Dentro do container:
flask run                    # Flask já está rodando
python -m pytest tests/      # Testes (Sprint 6)
```

### Nginx
```bash
# Ver logs do nginx
docker compose logs nginx

# Recarregar config
docker compose restart nginx
```

---

## 🔍 Health Check

```bash
# Verificar se tudo está rodando
curl http://localhost/api/health

# Resposta esperada:
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-05-29T11:17:00Z",
  "components": {
    "api": "operational",
    "backend": "operational"
  }
}
```

---

## 📝 Variáveis de Ambiente

Crie um arquivo `.env` na raiz (veja `.env.example`):

```env
# Supabase (Sprint 1)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-anon-key-aqui

# Flask
FLASK_ENV=development
DEBUG=1
```

**IMPORTANTE:** Nunca comite `.env` em produção!

---

## 📊 Monitoramento

```bash
# Ver logs de todos os containers
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f nginx
```

---

## 🐛 Troubleshooting

### "Port 80 already in use"
```bash
# Mude a porta no docker-compose.yml:
ports:
  - "8080:80"  # Acesse http://localhost:8080
```

### "Frontend not responding"
```bash
# Verifique se o dev server está rodando:
docker compose logs frontend

# Recrie o container:
docker compose down
docker compose up --build frontend
```

### "Backend connection refused"
```bash
# Verifique se o Flask está rodando:
docker compose logs backend

# Teste o health endpoint:
curl http://localhost/api/health
```

---

## 🚀 Deploy (Sprint 6)

Para deploy em OCI ou outro servidor:

```bash
# Build das imagens
docker build -t simples-editor-frontend -f docker/frontend.Dockerfile .
docker build -t simples-editor-backend -f docker/backend.Dockerfile .

# Adicione tags de registry (ex: Docker Hub)
docker tag simples-editor-frontend seu-user/simples-editor-frontend:latest
docker push seu-user/simples-editor-frontend:latest
```

---

## 📚 Links Úteis

- [Issues](https://github.com/celsohd21/simples_editor/issues)
- [Project Board](https://github.com/celsohd21/simples_editor/projects/1)
- [PRD](PRD_simples_editor.md)
- [Sprints](SPRINTS.md)

---

## 📝 Versionamento

- **v1.0.0** - Sprint 1: Foundation & Auth
- Próximas: Sprint 2-6 (veja SPRINTS.md)

---

## 👥 Contribuindo

1. Crie uma branch: `git checkout -b feature/meu-recurso`
2. Faça commit: `git commit -m "Add: minha feature"`
3. Push: `git push origin feature/meu-recurso`
4. Abra PR para review

---

**Status: ✅ Sprint 1 - Foundation & Auth — Issue #2 Completa**
