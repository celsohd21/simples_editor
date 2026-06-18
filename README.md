# Simples Editor

> Web IDE para a linguagem **SIMPLES** — escreva, compile e execute programas direto no navegador, sem instalação local.

[![Licença](https://img.shields.io/badge/licença-MIT-blue)](#licença)
![Status](https://img.shields.io/badge/status-concluído-brightgreen)

---

## Funcionalidades

- **Editor SIMPLES** com Monaco — syntax highlighting das 27 keywords, snippets, tema dark
- **Painel NASM** — assembly x86 gerado lado a lado com o código fonte
- **Terminal interativo** — xterm.js com suporte a `leia` (stdin) via WebSocket
- **Pipeline completo** — `simplesc` → `nasm` → `ld` → execução em sandbox Docker
- **Stop / Cancel** — interrompe execução em andamento (SIGTERM → SIGKILL)
- **Timeout automático** — 3 camadas (compile 15s, exec 10s, Docker 12s)
- **Error markers** — erros de compilação destacados no editor (linha/coluna)
- **Sandbox seguro** — 9 camadas de isolamento (sem rede, sem escrita, sem privilégios)
- **Rate limiting** — 300 requisições/hora por usuário
- **Métricas Prometheus** — compilações, execuções, latência, rate limits
- **Logs estruturados** — JSON via structlog para diagnóstico rápido

---

## Stack Técnica

| Camada | Tecnologia | Versão |
|---|---|---|
| **Frontend** | React + Vite + TypeScript | 18 / 5 / 5 |
| **Editor** | Monaco Editor | 0.50 |
| **Terminal** | xterm.js + xterm-addon-fit | 5.x |
| **Backend** | Python + Flask + flask-sock | 3.11 / 3.x |
| **Logs** | structlog | 24.x |
| **Métricas** | prometheus-client | 0.19 |
| **Auth** | Supabase (JWT) | — |
| **Proxy** | Nginx (Alpine) | 1.25+ |
| **Container** | Docker + Docker Compose | 24+ / v2 |
| **Compilador** | simplesc (C) + NASM + binutils-i686 + qemu-user-static | — |
| **Deploy** | Oracle Cloud Ampere A1 (ARM64) | Always Free |

---

## Quickstart

### Pré-requisitos

- [Docker](https://docs.docker.com/engine/install/) ≥ 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.0
- Conta [Supabase](https://supabase.com) (free tier) com um projeto criado

### Setup

```bash
# 1. Clone
git clone https://github.com/celsohd21/simples_editor.git
cd simples_editor

# 2. Configure o .env
cp .env.example .env
# Edite .env com SUPABASE_URL e SUPABASE_KEY do seu projeto Supabase

# 3. Suba os containers
docker compose up --build

# 4. Acesse
http://localhost
```

O build inicial leva de 3-5 minutos. Nas próximas execuções, o cache do Docker torna quase instantâneo.

### Fluxo básico

1. **Cadastre-se** em `http://localhost` (email + senha)
2. **Escreva** um programa SIMPLES no editor
3. **Clique em Run** — veja o NASM gerado no painel direito e a saída no terminal
4. **Interaja** com `leia` digitando no terminal
5. **Pare** a execução com o botão Stop se necessário

---

## Exemplo

### Entrada (SIMPLES)

```simples
programa fatorial
  inteiro n, fat, contador
inicio
  leia n
  fat <- 1
  contador <- 1
  enquanto contador < n faca
    contador <- contador + 1
    fat <- fat * contador
  fimenquanto
  escreva fat
fim
```

### Saída (Terminal)

```
5
120
[exit code: 0 — 0.07s]
```

---

## Arquitetura

```
Browser (React + Monaco + xterm.js)
│
├── HTTPS (auth, REST)
└── WSS (run, stdin, stdout)
        │
        ▼
Nginx (Reverse Proxy) — Porta 80
│
├── /api/*     → Frontend (React + Vite, :5173)
├── /ws/*      → Backend (Flask, :5000)
└── /metrics   → Bloqueado externamente (:9090 interno)
                        │
                        ▼
                Backend (Flask)
                ├── Auth (JWT verification)
                ├── Compilação (simplesc → nasm → ld)
                └── Execução (Docker sandbox)
                        │
                        ▼
            ┌─────────────────────────┐
            │ Sandbox Container       │
            │ --cap-drop=ALL          │
            │ --network=none          │
            │ --read-only             │
            │ --memory=256m           │
            │ --cpus=0.5              │
            │ Alpine + qemu-i386      │
            └─────────────────────────┘

Serviços externos: Supabase (Auth)
```

### Sandbox (9 camadas de segurança)

| Camada | Configuração |
|---|---|
| Container descartável | `docker run --rm` por execução |
| Sem rede | `--network=none` |
| FS imutável | `--read-only` + tmpfs `/tmp` (10 MB) |
| Memória | `--memory=256m` |
| CPU | `--cpus=0.5` (cgroups) |
| PIDs | `--pids-limit=64` (previne fork bomb) |
| Usuário | `--user=65534:65534` (nobody) |
| Capabilities | `--cap-drop=ALL` |
| Seccomp | Perfil padrão do Docker |

---

## API

### REST Endpoints

| Método | Path | Descrição | Auth |
|---|---|---|---|
| `GET` | `/api/health` | Health check público | ❌ |
| `POST` | `/api/auth/signup` | Cadastro | ❌ |
| `POST` | `/api/auth/login` | Login | ❌ |
| `POST` | `/api/auth/logout` | Logout | ✅ |
| `POST` | `/api/auth/verify` | Validar JWT | ✅ |
| `GET` | `/api/limits` | Limites do sistema | ❌ |
| `GET` | `/metrics` | Métricas Prometheus | Interno (porta 9090) |

### WebSocket `/ws/run`

**Handshake:** query param `?token=<jwt>`

**Cliente → Servidor:**

| Tipo | Descrição |
|---|---|
| `compile_and_run` | Inicia compilação + execução (`code` field) |
| `stdin` | Envia input para o binário (`data` field) |
| `stop` | Cancela execução |
| `ping` | Keepalive |

**Servidor → Cliente:**

| Tipo | Descrição |
|---|---|
| `compile_started` | Compilação iniciou |
| `compile_error` | Erro de compilação (`line`, `column`, `message`, `phase`) |
| `asm_generated` | NASM gerado (`asm` content) |
| `assemble_error` | Erro de montagem |
| `link_error` | Erro de linkagem |
| `exec_started` | Execução iniciou |
| `stdout` | Saída padrão (`data`) |
| `stderr` | Saída de erro (`data`) |
| `exit` | Execução finalizada (`code`, `duration_ms`) |
| `timeout` | Timeout atingido (`limit_s`) |
| `internal_error` | Erro interno |
| `pong` | Resposta ao ping |

---

## Desenvolvimento

### Testes

```bash
# Backend (pytest)
docker compose exec backend python -m pytest tests/ -v

# Backend com cobertura
docker compose exec backend python -m pytest tests/ --cov=src --cov-report=term

# E2E (Playwright)
docker compose exec frontend npx playwright test

# Segurança (valida sandbox)
docker compose exec backend python /app/backend/security_tests.py
```

### Lint

```bash
# Frontend (ESLint)
docker compose exec frontend npm run lint
```

### Comandos úteis

```bash
# Logs em tempo real
docker compose logs -f

# Shell no backend
docker compose exec backend bash

# Shell no frontend
docker compose exec frontend sh

# Reiniciar serviço
docker compose restart backend

# Derrubar tudo
docker compose down
```

---

## Deploy (OCI Ampere A1)

O deploy alvo é **Oracle Cloud Ampere A1 (ARM64)** — Always Free tier (4 OCPU / 24 GB RAM).

```bash
# Na VM (Ubuntu 22.04):
git clone https://github.com/celsohd21/simples_editor.git
cd simples_editor
cp .env.example .env
# Edite .env com SUPABASE_URL e SUPABASE_KEY
docker compose up --build -d
```

**Atenção:** Ubuntu 22.04 no OCI bloqueia portas 80/443 no `iptables` por padrão. Libere com:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

Mais detalhes no [PRD](PRD_simples_editor.md).

---

## Estrutura do Projeto

```
simples_editor/
├── docker/
│   ├── nginx.Dockerfile        # Reverse proxy
│   ├── frontend.Dockerfile     # React + Vite
│   ├── backend.Dockerfile      # Flask + toolchain
│   ├── executor.Dockerfile     # Sandbox mínimo (Alpine)
│   └── nginx.conf              # Rotas
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Componente principal
│   │   ├── components/
│   │   │   ├── EditorPage.jsx  # Layout 3 painéis
│   │   │   ├── Editor.jsx      # Monaco Editor
│   │   │   └── NasmPanel.jsx   # Painel NASM
│   │   ├── languages/
│   │   │   ├── simples.js      # Tokenizer SIMPLES
│   │   │   └── nasm.js         # Tokenizer NASM
│   │   ├── pages/
│   │   │   └── LoginPage.jsx   # Tela de login
│   │   └── main.jsx            # Entry point
│   └── e2e/
│       └── simples-editor.spec.js  # Testes Playwright
├── backend/
│   ├── src/
│   │   ├── app.py              # Flask app
│   │   ├── execution.py        # Estratégias de execução
│   │   ├── ws_handlers.py      # WebSocket handler
│   │   ├── auth.py             # JWT decorator
│   │   ├── auth_endpoints.py   # Endpoints de auth
│   │   ├── logging_config.py   # structlog config
│   │   └── metrics.py          # Prometheus metrics
│   ├── tests/                  # Testes pytest
│   ├── security_tests.py       # Validação do sandbox
│   └── verify_logging.py       # Verificação de logs
├── simples-compiler/
│   └── src/                    # Compilador SIMPLES (C)
├── docs/
│   ├── AUDIT.md                # Auditoria de segurança
│   ├── INCIDENTS.md            # Plano de resposta
│   ├── RETROSPECTIVA.md        # Retrospectiva da equipe
│   └── APRESENTACAO.md         # Slides da apresentação
├── docker-compose.yml          # Orquestração
├── .env.example                # Template de variáveis
└── PRD_simples_editor.md       # Product Requirements
```

---

## Troubleshooting

| Problema | Solução |
|---|---|
| **Porta 80 ocupada** | Altere `"80:80"` para `"8080:80"` no `docker-compose.yml` |
| **Frontend não responde** | `docker compose logs frontend` e depois `docker compose restart frontend` |
| **Backend connection refused** | `docker compose logs backend` e verifique se `flask run` está rodando |
| **Container não sobe** | `docker compose down && docker compose up --build` |
| **Erro de permissão Docker** | Adicione seu usuário ao grupo docker: `sudo usermod -aG docker $USER` |
| **Timeout de execução** | O limite padrão é 10s. Ajuste `EXEC_TIMEOUT_S` no `.env` |

---

## Links

- [Issues](https://github.com/celsohd21/simples_editor/issues)
- [Project Board](https://github.com/celsohd21/simples_editor/projects)
- [PRD](PRD_simples_editor.md)
- [Sprints](SPRINTS.md)
- [Auditoria de Segurança](docs/AUDIT.md)
- [Plano de Resposta a Incidentes](docs/INCIDENTS.md)
- [Retrospectiva](docs/RETROSPECTIVA.md)
- [Apresentação](docs/APRESENTACAO.md)

---

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para mais informações.

---

## Créditos

- **Celso Oliveira** — Lead Developer (arquitetura, frontend, backend, Docker, CI/CD, deploy)
- **Gianlucca Sagio** — Developer (Sprint 5: hardening, métricas, timeouts, testes de segurança)
- **Paulo Muniz de Ávila** — Developer (documentação, PRs, compilador SIMPLES)
- **Prof. Orientador** — Orientação e requisitos

---

## Status do Projeto

✅ **Sprint 6 concluída** — Projeto finalizado para apresentação.

| Sprint | Foco | Status |
|---|---|---|
| 1 | Foundation & Auth | ✅ |
| 2 | Editor & NASM Panel | ✅ |
| 3 | Compilation Pipeline | ✅ |
| 4 | Interactive Execution | ✅ |
| 5 | Hardening & Observability | ✅ |
| 6 | Polish & Deploy | ✅ |
