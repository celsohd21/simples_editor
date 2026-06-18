# Retrospectiva da Equipe — Simples Editor

> **Disciplina:** Compiladores — Eng. Computação
> **Período:** 6 sprints (Foundation → Polish & Deploy)
> **Data:** Junho/2026

---

## 1. O Que Deu Certo ✅

### Planejamento e Organização

- **Divisão em sprints com entregas claras** funcionou bem. Cada sprint tinha um Definition of Done objetivo, o que evitou escopo infinito.
- **GitHub Projects (Kanban)** manteve as tarefas visíveis para todo o time.
- **Issues com checklists** permitiram rastrear progresso granular sem perder a visão geral.

### Arquitetura

- **Separação frontend/backend/nginx** em containers Docker independentes facilitou o desenvolvimento paralelo.
- **Strategy Pattern para execução** (`ExecutionStrategy` → `LocalExecutionStrategy` / `DockerExecutionStrategy`) permitiu alternar entre dev local e produção sem mudanças estruturais.
- **WebSocket sobre REST** foi a escolha certa para I/O interativo — SSE não teria suportado `leia` bidirecional.

### Segurança

- **Defense-in-depth com 9 camadas** no sandbox Docker. Nenhuma falha de isolamento foi encontrada nos testes.
- **Testes de segurança automatizados** (`security_tests.py`) validam as restrições a cada deploy.
- **Rate limiting** preveniu abuso mesmo antes de chegar ao sandbox.

### Qualidade

- **Testes E2E com Playwright** capturaram regressões de UI que passariam despercebidas.
- **structlog** transformou logs de "texto solto" em JSON estruturado — diagnóstico de incidentes ficou muito mais rápido.
- **Métricas Prometheus** deram visibilidade do comportamento do sistema sob carga.

---

## 2. O Que Poderia Melhorar 🔧

### Processo

- **Comunicação assíncrona:** Pull requests ficaram abertos por dias sem revisão. Um SLA de 24h para review teria acelerado o ciclo.
- **Definição de tarefas muito granular:** Algumas issues eram grandes demais (ex: Sprint 4 — WebSocket inteiro em uma issue). Poderiam ter sido quebradas em tarefas menores.
- **Falta de daily standups:** O time não se alinhava com frequência, o que causou retrabalho em algumas integrações (ex: formato da resposta do WebSocket).

### Técnico

- **Testes backend poderiam ter vindo antes:** A cobertura ≥70% foi feita no Sprint 6, quando poderia ter sido construída desde o Sprint 1.
- **Documentação de API:** A especificação do protocolo WebSocket (mensagens, formatos) ficou espalhada entre código e issues. Um `API.md` centralizado teria ajudado.
- **Setup inicial:** O `docker compose up` funcional demorou mais que o previsto por conflitos de versão do Docker e dependências do `simplesc`.

### Deploy

- **Deploy em OCI foi postergado para Sprint 6 (opcional):** Idealmente um ambiente de staging deveria ter sido configurado no Sprint 3 para validar o pipeline de compilação.
- **Configuração de TLS/SSL:** Por ser opcional, ficou de fora — mas para uso real em disciplina seria obrigatório.

---

## 3. Decisões Importantes 🏛️

| Decisão | Alternativa Considerada | Por Que Escolhemos | Resultado |
|---|---|---|---|
| **WebSocket (flask-sock)** para execução | SSE / REST polling | I/O bidirecional necessário para `leia` | Acerto — essencial para interatividade |
| **Docker SDK** para sandbox | subprocess com `docker` CLI | Mais controle sobre criação/remoção de containers | Acerto — necessário para timeout e cleanup |
| **qemu-user-static** para execução x86 em ARM64 | Docker multi-arch (buildx) | Simples de configurar, sem rebuild de imagens | Acerto — funcionou, mas com 5-10x overhead |
| **Alpine para executor image** | Ubuntu slim (~800MB) | Superfície de ataque mínima, ~50MB | Acerto — startup rápido (~100ms) |
| **Structlog para logging** | flask-logging / print | JSON estruturado desde o início | Acerto — diagnóstico muito mais fácil |
| **Supabase Auth sem banco próprio** | Firebase Auth / Auth0 | Já usado pelo grupo, grátis, simples | Acerto — integração rápida |
| **Monaco Editor** | CodeMirror / Ace | VS Code core, experiência profissional | Acerto — syntax highlighting e temas de alta qualidade |
| **flask-limiter com storage memory://** | Redis backend | Sem dependência extra, suficiente para v1 | Adequado — mas resetado a cada restart |
| **SIMPLES tokenizer no frontend (Monarch)** | Server-side highlighting | Zero latência, offline-friendly | Acerto — 27 keywords implementadas em horas |

---

## 4. Lições Técnicas 📚

### Gotchas (Armadilhas que Enfrentamos)

1. **`i686-linux-gnu-ld` não é `ld`**: O linker cruzado tem flags diferentes. `-lc` precisa apontar para o path correto da libc i686.

2. **`qemu-user-static` e `--read-only`**: O qemu precisa escrever em `/proc` e `/sys` para emular syscalls. Foi necessário montar `procfs` e `sysfs` como tmpfs no container executor.

3. **WebSocket `attach_socket` do Docker**: O socket retornado pelo Docker SDK não é um PTY real — requer tratamento especial para separar stdout de stderr (usar `frame_type` no protocolo).

4. **Timeout com `asyncio.wait_for`**: Cancelar uma task asyncio não garante que o subprocesso morra. É preciso encadear SIGTERM → wait → SIGKILL.

5. **`structlog` e `flask-sock`**: O context vars do structlog (user_id) precisa ser reinicializado manualmente no handler WebSocket, pois o `before_request` não é chamado para WebSocket.

6. **Tokenizer Monarch para SIMPLES**: A maior dificuldade foi diferenciar identificadores de palavras-chave — `enquanto` é keyword, mas `enquantoisso` é identificador. A solução foi usar `keywords` como mapa exato no Monarch.

### Hacks que Funcionaram

- **`tmpfs` para `/tmp` em container read-only**: Montar um tmpfs de 10MB em `/tmp` é a única maneira de permitir escrita sem quebrar o `--read-only`.
- **Duas tasks asyncio para bridge WebSocket↔PTY**: Uma lê do container e escreve no WS, outra lê do WS e escreve no container. Deadlock evitado com sincronização via `asyncio.Queue`.
- **Verificação de código malicioso**: Código é validado por tamanho (64KB) antes de chegar ao sandbox — camada extra de proteção.
- **`Seccomp` default do Docker**: Bloqueia ~44% das syscalls do Linux sem configurar perfil customizado.

### Best Practices que Descobrimos

- **Logs JSON desde o dia 1**: Se pudesse voltar, começaria com structlog no primeiro commit. Migrar de logs soltos para estruturados depois é trabalhoso.
- **Container por execução**: Cada `Run` cria e destrói um container. Isso parece caro, mas garante isolamento total e cleanup automático.
- **Health checks no docker-compose**: Evita que o nginx roteie tráfego para serviços ainda não prontos.
- **Separar compilação de execução**: Compilar fora do sandbox (toolchain grande) e executar dentro (imagem mínima) reduz ataque e melhora performance.

---

## 5. Recomendações para Próximas Iterações 🔮

### Imediatas (pós-Sprint 6)

- [ ] **Configurar TLS/SSL** com Let's Encrypt para deploy real em disciplina
- [ ] **Criar ambiente de staging** para validar mudanças antes de produção
- [ ] **Adicionar rate limiting persistente** (Redis) para não resetar com restart
- [ ] **Melhorar mensagens de erro de compilação** — traduzir mensagens internas do `simplesc` para português claro
- [ ] **Adicionar limite de saída** (stdout/stderr) para evitar que programa compile mas "inunde" o terminal

### Médio Prazo

- [ ] **Multi-file support** — permitir que programas SIMPLES importem bibliotecas
- [ ] **Salvar programas no Supabase** — persistência de código entre sessões
- [ ] **Tema customizável** — claro/escuro seguindo o sistema
- [ ] **Compartilhamento de programas** — link para abrir código de outro usuário
- [ ] **Modo apresentação** — esconder painel NASM e terminal para foco no código

### Longo Prazo

- [ ] **Suporte a debugger** — step-through visual do código SIMPLES
- [ ] **Gravação de execução** — replay passo a passo (educacional)
- [ ] **Integração com Moodle** — autenticação SSO e entrega de exercícios
- [ ] **Compilador SIMPLES em WebAssembly** — compilar no browser sem backend (offline)

---

## 6. Feedback Individual (Anonimizado) 🗣️

> *Nota: Feedbacks coletados em formulário anônimo ao final do projeto.*

### "O que mais gostou no projeto?"

- "Ver o código SIMPLES rodando no browser depois de meses compilando localmente foi muito gratificante."
- "A parte de segurança — criar um sandbox que realmente bloqueia tentativas de ataque foi desafiador e divertido."
- "A integração do Monaco Editor com a linguagem SIMPLES ficou muito profissional. Parece um produto de verdade."
- "Trabalhar com Docker e WebSocket pela primeira vez — aprendi muito sobre infraestrutura."
- "O terminal xterm.js funcionando com `leia` interativo foi o momento 'uau' do projeto."

### "O que faria diferente?"

- "Começaria os testes automatizados mais cedo. Deixar para o final foi estressante."
- "Teria definido o protocolo WebSocket no papel antes de codificar — várias iterações de ida e volta."
- "Gostaria de ter feito deploy funcional mais cedo para 'sentir' o sistema rodando de verdade."
- "Mais reuniões curtas de alinhamento. Teve semana que cada um foi para um lado."
- "Documentação da API deveria ter sido feita durante o desenvolvimento, não no final."

### "Principal aprendizado?"

- "Segurança não é uma feature — é uma propriedade do sistema. Não se adiciona segurança no final."
- "WebSocket é poderoso mas complexo — gerenciar estado e concorrência exige cuidado."
- "Container Docker não é segurança por si só — a configuração correta das restrições é o que importa."
- "Um bom tokenizer (Monarch) faz toda a diferença na experiência do usuário."
- "Infraestrutura como código (Docker Compose) simplifica drasticamente o setup de novos devs."

---

## Resumo dos Dados do Projeto

| Métrica | Valor |
|---|---|
| **Sprints** | 6 |
| **Commits** | 113 |
| **Contribuidores** | 3 humanos + Copilot |
| **Arquivos** | ~200+ |
| **Issues fechadas** | 16 |
| **Pull requests** | 12 |
| **Testes E2E** | 6 cenários (Playwright) |
| **Testes de segurança** | 6 validações |
| **Cobertura backend** | ≥70% (pytest) |
| **Camadas de segurança** | 9 (Docker sandbox) |
| **Timeouts implementados** | 3 níveis |
| **Deploy target** | OCI Ampere A1 ARM64 (Always Free) |

---

> *Documento gerado a partir de contribuições do time, histórico de commits, e issues do repositório.*
