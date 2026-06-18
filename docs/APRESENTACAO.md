# Simples Editor — Apresentação Final

> **Disciplina:** Compiladores — Engenharia de Computação
> **Instituição:** IFSULDEMINAS — Poços de Caldas
> **Duração:** 15-20 min (apresentação oral)

---

## 1. O Problema

**"Tenho que compilar e executar um programa SIMPLES. Como eu faço?"**

### Antes (Fluxo Manual)

- Instalar Linux 32-bit (VM/WSL)
- Compilar com `simplesc`
- Montar com `nasm -f elf32`
- Linkar com `ld` (i686)
- Executar binário localmente
- Zero suporte a `leia` (stdin)

### Atrito

- Setup complexo para cada aluno
- Ambiente diferente por SO
- Sem feedback visual imediato
- Dificuldade de diagnosticar erros
- Baixa adesão à prática

**Objetivo:** Zero instalação local. Tudo no browser.

---

## 2. A Solução

Web IDE com **3 painéis simultâneos**:

| Painel | Funcionalidade |
|---|---|
| **📝 Editor SIMPLES** | Monaco Editor com syntax highlighting para 27 keywords, snippets, tema dark |
| **⚙️ NASM Panel** | Assembly x86 gerado lado a lado com o código fonte original |
| **💻 Terminal** | xterm.js interativo com suporte a `leia` (stdin) via WebSocket |

### Fluxo completo

1. Aluno faz login (email/senha via Supabase Auth)
2. Escreve código SIMPLES no editor Monaco
3. Clica em **Run**
4. Código é enviado via WebSocket para o backend Flask
5. Backend compila: `simplesc` → NASM `.asm`
6. Backend monta: `nasm -f elf32` → `.o`
7. Backend linka: `i686-linux-gnu-ld` → executável ELF
8. Backend executa em container Docker sandboxizado com `qemu-user-static`
9. Saída streamada em tempo real para o xterm.js via WebSocket
10. Aluno pode interagir com `leia` (stdin) pelo terminal

---

## 3. Stack Técnica

### Frontend

- **React 18** — UI framework
- **Vite 5** — Build tool / dev server
- **TypeScript 5** — Type safety
- **Monaco Editor 0.50** — Editor de código (VS Code core)
- **xterm.js 5** — Terminal emulador
- **react-resizable-panels** — Painéis redimensionáveis
- **Playwright 1.61** — E2E testing

### Backend

- **Python 3.11+** — Runtime
- **Flask 3** — REST API framework
- **flask-sock 0.7** — WebSocket support
- **structlog 24** — Structured JSON logging
- **prometheus-client** — Métricas
- **docker SDK 7** — Gerenciamento de containers
- **flask-limiter 3.5** — Rate limiting
- **PyJWT** — Validação de tokens JWT

### Compilador / Toolchain

- **simplesc** (C) — Compilador SIMPLES → NASM
- **NASM** — Assembler x86 (`nasm -f elf32`)
- **binutils-i686-linux-gnu** — Linkeditor cruzado
- **qemu-user-static** — Emulação x86 em ARM64
- **GCC / Make** — Build do `simplesc`

### Infraestrutura

- **Docker 24+ / Docker Compose v2** — Containerização
- **Nginx 1.25+ (Alpine)** — Reverse proxy, WebSocket upgrade
- **Supabase (cloud)** — Autenticação (JWT, email/password)
- **Oracle Cloud Ampere A1 (ARM64)** — Deploy (Always Free tier)
- **Prometheus** — Métricas em `/metrics` (porta 9090)
- **GitHub Actions** — CI/CD (E2E tests)

---

## 4. Arquitetura

```
Browser (React + Monaco + xterm.js)
│
├── HTTPS (auth, REST)
└── WSS (run, stdin, stdout)
        │
        ▼
Nginx (Reverse Proxy) — Porta 80
│
├── /api/* → Frontend (React + Vite, porta 5173)
└── /ws/*  → Backend (Flask, porta 5000)
                │
                ▼
        Sandbox Docker
        ──────────────
        --cap-drop=ALL
        --network=none
        --read-only
        --memory=256m
        --cpus=0.5
        ──────────────
        Alpine + qemu-i386
        (emula binário x86)
```

**Serviços (docker-compose.yml):**
- **nginx**: Proxy reverso (porta 80, metrics em 9090 com ACL)
- **frontend**: React + Vite (porta 5173, não exposta)
- **backend**: Flask + toolchain (porta 5000, não exposta)
- Rede interna: `simples-network` (bridge)

**Autenticação:** Supabase Auth → JWT → `@verify_jwt` decorator

**Observabilidade:**
- Logs estruturados JSON via `structlog` (stdout)
- Métricas Prometheus: `compilations_total`, `executions_total`, `latency_ms`, `rate_limits_total`

---

## 5. Demo

> ▶️ **Vídeo de demonstração (1-2 min)**
>
> *Inserir link do YouTube/Google Drive com gravação de tela mostrando:*

| Etapa | Descrição |
|---|---|
| 1 | Login com email/senha |
| 2 | Escrever programa SIMPLES no editor |
| 3 | Clicar em Run |
| 4 | Ver assembly NASM gerado no painel direito |
| 5 | Interagir com `leia` via terminal |
| 6 | Ver saída `escreva` no terminal |
| 7 | Testar o botão Stop |
| 8 | Testar timeout (programa com loop infinito) |

**Ferramentas sugeridas:** OBS Studio, Loom, ou QuickTime Player.

---

## 6. Principais Desafios

### 🧩 x86 32-bit em ARM64 (Oracle Ampere A1)

**Problema:** O compilador `simplesc` gera código x86 32-bit (`int 0x80`), mas o deploy é em ARM64 (Oracle Ampere A1).

**Solução:** `qemu-user-static` dentro do sandbox Docker emula as instruções x86. Overhead de 5-10x, aceitável para programas didáticos pequenos.

---

### 🔌 I/O interativo via WebSocket + PTY

**Problema:** O comando `leia` precisa de stdin bidirecional em tempo real. REST e SSE não suportam isso.

**Solução:** WebSocket (`/ws/run`) com `flask-sock` + duas tasks asyncio concorrentes: `pty_to_ws()` (container → browser) e `ws_to_pty()` (browser → container).

---

### 🛡️ Sandbox multi-camadas (defense-in-depth)

**Problema:** Código de aluno pode ser malicioso — fork bombs, exaustão de memória, tentativas de rede.

**Solução:** 9 layers de segurança no container Docker:

| Camada | Configuração |
|---|---|
| 1 | Container por execução (descartável) |
| 2 | `--network=none` — sem rede |
| 3 | `--read-only` + tmpfs `/tmp` — FS imutável |
| 4 | `--memory=256m` — limite de memória |
| 5 | `--cpus=0.5` — limite de CPU (cgroups) |
| 6 | `--pids-limit=64` — previne fork bomb |
| 7 | `--user=65534:65534` — nobody user |
| 8 | `--cap-drop=ALL` — sem capacidades Linux |
| 9 | Seccomp default profile — syscalls perigosos bloqueados |

---

### ⏱️ Timeout em 3 camadas

**Problema:** Loop infinito poderia travar o servidor.

**Solução:**
1. **Compile timeout:** 15s (`subprocess.run(timeout=15)`)
2. **Execution wall-clock:** 10s (`asyncio.wait_for`)
3. **Docker hard limit:** `--stop-timeout=12`
4. Graceful shutdown: SIGTERM → 1s wait → SIGKILL

---

### 🔄 Pipeline cross-platform

**Problema:** `simplesc` gera NASM para x86 32-bit, mas o host pode ser x86_64 ou ARM64.

**Solução:**
- NASM é nativamente cross-assembler (qualquer arch → x86)
- `binutils-i686-linux-gnu` fornece linkeditor cruzado
- `qemu-user-static` executa o binário x86 em qualquer arch

---

## 7. Lições Aprendidas

### Frontend

- Monaco Monarch tokenizer é poderoso para DSLs educacionais — 27 keywords implementadas puramente no client-side
- `react-resizable-panels` simplifica layouts complexos com 3 painéis redimensionáveis
- xterm.js + WebSocket é a melhor combinação para terminal interativo no browser
- Playwright E2E tests pegam regressões de UI que passariam despercebidas

### Backend

- WebSocket sobre REST foi essencial para I/O interativo (`leia`)
- Strategy Pattern (`ExecutionStrategy` base → `LocalExecutionStrategy` / `DockerExecutionStrategy`) simplificou a alternância entre dev e produção
- structlog com saída JSON pagou dividendos no diagnóstico de incidentes
- Rate limiting (`flask-limiter`) é crítico em ambiente compartilhado com 50+ alunos

### DevOps

- Segurança precisa ser **defense-in-depth** — nenhuma camada isolada é suficiente
- Cross-platform (x86 → ARM64) exige planejamento desde o início do projeto
- OCI Ampere A1 Always Free (4 OCPU / 24 GB RAM) é viável para uso acadêmico com budgeting cuidadoso
- Ubuntu 22.04 no OCI tem `iptables` bloqueando portas 80/443 por padrão — documentado como risco no PRD

### Gerais

- Terraform para infraestrutura reproduzível desde o início (PRD inclui config completa)
- qemu-user-static adiciona 5-10x overhead — aceitável para programas didáticos de até 10s
- Documentação de incidentes (`docs/INCIDENTS.md`) reduz tempo de resposta em sala de aula
- Testes de segurança automatizados (`security_tests.py`) validam o sandbox a cada deploy

---

## 8. Linha do Tempo (Sprints)

| Sprint | Foco | Entregas |
|---|---|---|
| **Sprint 1** | Fundação & Auth | Docker Compose, Supabase Auth, JWT, health endpoint |
| **Sprint 2** | Editor & NASM Panel | Monaco, tokenizer SIMPLES (27 keywords), 3 painéis, resizable |
| **Sprint 3** | Pipeline de Compilação | `simplesc` + `nasm` + `ld`, compile timeout, error markers |
| **Sprint 4** | Execução Interativa | WebSocket, xterm.js, PTY bridge, qemu-user, `leia` |
| **Sprint 5** | Hardening & Observability | structlog, timeouts, Prometheus, rate limiting, sandbox 9 camadas, incidentes |
| **Sprint 6** | Polish & Deploy | E2E tests, README, demo, OCI deploy, apresentação final |

---

## 9. Time

| Membro | Papel | Contribuições |
|---|---|---|
| **Celso Oliveira** | Lead Developer | Arquitetura, Frontend, Backend, Docker, CI/CD, Deploy |
| **Gianlucca Sagio** | Developer | Sprint 5: hardening, métricas, timeouts, testes de segurança |
| **Paulo Muniz de Avila** | Developer | Documentação, PRs, compilador SIMPLES (`simplesc`) |
| **Prof. Orientador** | Orientação | Requisitos, acompanhamento, avaliação |

---

## 10. Resultado Final

### Funcionalidades implementadas

- [x] Autenticação (Supabase Auth + JWT)
- [x] Editor Monaco com syntax highlighting SIMPLES (27 keywords)
- [x] Painel NASM com assembly gerado lado a lado
- [x] Terminal xterm.js interativo com WebSocket
- [x] Pipeline completo: `simplesc` → `nasm` → `ld` → execução
- [x] Error markers no editor (linha/coluna)
- [x] Botão Stop (SIGTERM)
- [x] Timeout automático (3 camadas: 15s + 10s + 12s)
- [x] Sandbox Docker com 9 layers de segurança
- [x] Logs estruturados (structlog JSON)
- [x] Métricas Prometheus
- [x] Rate limiting (300/h, 1000/dia)
- [x] Testes de segurança automatizados
- [x] Plano de resposta a incidentes
- [x] E2E tests com Playwright
- [x] CI/CD com GitHub Actions
- [x] Suporte multi-arch (x86_64 + ARM64)

### Screenshots

> *Inserir capturas de tela da aplicação:*
> - Tela de login
> - Editor com código SIMPLES
> - NASM panel com assembly
> - Terminal com saída de execução
> - Error markers durante compilação
> - Métricas Prometheus

---

## Obrigado!

**Perguntas?**

GitHub: [github.com/celsohd21/simples_editor](https://github.com/celsohd21/simples_editor)
