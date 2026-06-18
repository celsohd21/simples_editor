# Plano de Resposta a Incidentes (Sprint 5)

Este documento define o plano de resposta a incidentes para o ambiente de produção do **Simples Editor**. Abrange desde a detecção até a resolução e o playbook de cleanup pós-incidente.

## Escalação

| Nível | Quem | Responsabilidade | Contato |
|---|---|---|---|
| **L1** | Aluno / Usuário | Reportar comportamento anômalo | N/A |
| **L2** | Professor / Monitor | Diagnosticar logs, escalar para admin | Conforme canal da disciplina |
| **L3** | Admin (DevOps) | Acessar servidor, reiniciar serviços, alterar configurações | Conforme canal da disciplina |

## Logs a Consultar

Todos os logs do backend são estruturados em JSON via `structlog` e emitidos para **stdout**. O acesso é feito via `docker compose logs`.

```bash
# Logs do backend
docker compose logs backend

# Logs em tempo real
docker compose logs -f backend

# Filtrar por usuário específico
docker compose logs backend | Select-String '"user_id": "uuid-do-usuario"'

# Filtrar por evento
docker compose logs backend | Select-String '"event": "execution_timeout"'

# Filtrar por erro
docker compose logs backend | Select-String '"error"'
```

### Campos do Log Estruturado

| Campo | Descrição |
|---|---|
| `timestamp` | ISO 8601 do evento |
| `user_id` | UUID do usuário autenticado (ou `anonymous`) |
| `event` | Nome do evento (`execution_started`, `execution_timeout`, `compile_failed`, etc.) |
| `status` | `success`, `timeout`, `error`, `stop` |
| `latency_ms` | Duração em milissegundos |
| `error` | Mensagem de erro (se houver) |
| `code_size` | Tamanho do código submetido em bytes |

### Métricas do Prometheus (porta 9090)

```bash
# Acesso restrito a IPs internos
curl http://127.0.0.1:9090/metrics

# Métricas disponíveis:
# - compilations_total{status="success|timeout|error"}
# - executions_total{status="success|timeout|error|stop"}
# - latency_ms_bucket{method, endpoint}
# - rate_limits_total
```

---

## Cenários de Incidente

### 1. Loop Infinito (Timeout de Execução)

**Sintomas:**
- Usuário reporta que o programa "nunca termina"
- Logs mostram `"event": "execution_timeout"` com `latency_ms` próximo de `EXEC_TIMEOUT_S` (10s)

**O que acontece:**
- O `TimeoutExecutor` (ou `subprocess.run(timeout=)`) interrompe o processo após 10s
- Envia SIGTERM, aguarda 1s, depois SIGKILL se necessário
- Container Docker é removido automaticamente

**O que fazer:**
1. Verificar logs do backend:
   ```bash
   docker compose logs backend | Select-String '"event": "execution_timeout"'
   ```
2. Confirmar que o timeout está configurado corretamente (endpoint `GET /api/limits`)
3. Se o timeout não estiver sendo respeitado, verificar variáveis de ambiente:
   ```bash
   docker compose exec backend env | Select-String TIMEOUT
   ```

**Logs a consultar:**
- `execution_timeout` — timeout atingido
- `exec_kill` — processo morto após SIGKILL
- `exec_stop` — usuário solicitou parada manual

**Escalação:** L2 (professor) se o timeout não funcionar → L3 (admin) para ajustar `EXEC_TIMEOUT_S` no `.env` e reiniciar.

---

### 2. Exploit / Tentativa de Ataque (Sandbox Evasion)

**Sintomas:**
- Código tenta usar `socket`, `os.system`, `subprocess`, ou syscalls privilegiadas
- Logs mostram `"event": "compile_failed"` ou `"event": "execution_error"` com erros de permissão
- O sandbox Docker bloqueia a operação silenciosamente

**O que acontece:**
- `cap_drop=['ALL']` impede chamadas de sistema privilegiadas
- `network_mode='none'` bloqueia toda comunicação de rede
- `read_only=True` impede escrita fora de `/tmp`
- O erro é capturado e registrado como `execution_error`

**O que fazer:**
1. Coletar logs do usuário suspeito:
   ```bash
   docker compose logs backend | Select-String '"user_id": "<id>"'
   ```
2. Analisar o código submetido (campo `code_size` e contexto do log)
3. Verificar se o sandbox está ativo e configurado:
   ```bash
   docker compose exec backend python -c "from app import app; print('ok')"
   ```
4. Validar as regras de segurança executando `security_tests.py`:
   ```bash
   docker compose exec backend python /app/backend/security_tests.py
   ```

**Logs a consultar:**
- `execution_error` — erro na execução com detalhes
- `compile_failed` — falha na compilação (possível ofuscação)
- `code_validated` — validação de tamanho do código

**Escalação:**
- **Imediata:** L2 (professor) — bloquear usuário via Supabase se necessário
- **Crítica:** L3 (admin) — revisar configurações do Docker, verificar se há vazamento de containers

---

### 3. Tentativa de Acesso à Rede

**Sintomas:**
- Código tenta fazer requisições HTTP, DNS, ou conectar a IPs externos
- Logs de execução mostram `socket.error` ou `Connection refused`
- Nenhum tráfego de rede do container é observado

**O que acontece:**
- `network_mode='none'` no Docker elimina toda conectividade
- Tentativas de `socket()`, `connect()`, `send()` falham silenciosamente
- O erro é capturado e logado como `execution_error`

**O que fazer:**
1. Verificar logs de execução com erro de rede:
   ```bash
   docker compose logs backend | Select-String 'socket\|network\|connect'
   ```
2. Confirmar que nenhum container tem rede acidentalmente:
   ```bash
   docker inspect $(docker ps -q --filter name=simples-exec) | Select-String '"NetworkMode"'
   ```
3. Revisar logs do nginx para tráfego suspeito vindo de IPs externos:
   ```bash
   docker compose logs nginx | Select-String '403\|500'
   ```

**Logs a consultar:**
- `execution_error` com menção a `socket`/`network`
- Logs do nginx para padrões anômalos de requisição

**Escalação:** L2 (professor) → L3 (admin) se houver suspeita de falha no isolamento de rede.

---

### 4. DoS (Exaustão de Recursos)

**Sintomas:**
- Backend lento ou indisponível
- Múltiplos timeouts simultâneos
- Logs com `"event": "rate_limit_exceeded"` para múltiplos usuários
- Métricas de latência elevadas (`latency_ms` acima de 5s)

**O que acontece:**
- **Rate Limiting:** `flask-limiter` bloqueia requisições após `300/h` ou `1000/dia` por usuário/IP
- **Memória:** `mem_limit='256m'` no executor Docker impede OOM no host
- **CPU:** `cpus=0.5` limita cada execução a meio núcleo

**O que fazer (L1 - Professor):**
1. Verificar se o rate limiting está ativo:
   ```bash
   curl -I http://localhost/api/limits
   ```
2. Consultar métricas de rate limit:
   ```bash
   curl http://127.0.0.1:9090/metrics | Select-String rate_limits
   ```
3. Verificar logs de 429 (Too Many Requests):
   ```bash
   docker compose logs backend | Select-String '"status": "rate_limited"'
   ```
4. Se o rate limiting não estiver funcionando, verificar se `flask-limiter` está ativo no `app.py`.

**O que fazer (L3 - Admin) — Se o serviço estiver degradado:**

1. Verificar saúde dos serviços:
   ```bash
   docker compose ps
   docker compose exec backend curl -f http://localhost:5000/api/health
   ```
2. Verificar consumo de recursos:
   ```bash
   docker stats --no-stream
   ```
3. Se necessário, reiniciar o backend:
   ```bash
   docker compose restart backend
   ```
4. Em último caso, reconstruir e subir tudo:
   ```bash
   docker compose down
   docker compose up -d --build
   ```

**Logs a consultar:**
- `rate_limit_exceeded` — requisição bloqueada
- `execution_timeout` — possível indicador de contenção
- Latência acima do normal no histograma do Prometheus

**Escalação:**
- L2 (professor) para rate limiting por usuário abusivo
- L3 (admin) se o serviço inteiro estiver degradado

---

### 5. Vazamento de Containers (Orphans)

**Sintomas:**
- Containers fantasmas com prefixo `simples-exec-*` que persistem após execução
- Comando `docker ps -a` mostra múltiplos containers stopped/exited não removidos
- Logs de execução bem-sucedida mas container permanece no sistema

**Causas Possíveis:**
- Crash do backend durante a limpeza pós-execução
- Timeout na remoção do container (`remove=True` no `docker-py` não executado)
- Interrupção manual do processo do backend

**O que fazer:**
1. Listar containers órfãos:
   ```bash
   docker ps -a --filter name=simples-exec --format "table {{.ID}}\t{{.Status}}\t{{.CreatedAt}}"
   ```
2. Remover containers órfãos manualmente:
   ```bash
   docker rm $(docker ps -a -q --filter name=simples-exec)
   ```
3. Verificar se o backend está executando a limpeza corretamente nos logs:
   ```bash
   docker compose logs backend | Select-String '"event": "container_cleanup"'
   ```

**Escalação:** L2 (professor) → L3 (admin) se o problema for recorrente.

---

## Playbook de Cleanup

### Remover Containers Órfãos

```powershell
# Listar todos os containers relacionados à execução
docker ps -a --filter name=simples-exec

# Remover todos os containers parados com prefixo simples-exec
docker rm $(docker ps -a -q --filter name=simples-exec)

# Forçar remoção de containers travados
docker rm -f $(docker ps -a -q --filter name=simples-exec)

# Limpar containers que não são do compose
docker container prune -f
```

### Resetar Rate Limit

O rate limit atual usa armazenamento em memória (`storage_uri="memory://"`). Reiniciar o backend zera os contadores:

```bash
# Reset suave (reinicia apenas o backend)
docker compose restart backend

# Reset completo (derruba e sobe tudo)
docker compose down
docker compose up -d
```

### Limpeza Geral do Docker

```bash
# Remover containers parados, networks não usadas, imagens dangling
docker system prune -f

# Remover imagens não utilizadas (cuidado: pode levar tempo)
docker image prune -a -f

# Verificar espaço em disco
docker system df
```

### Verificação Pós-Cleanup

```bash
# Confirmar que não há containers órfãos
docker ps -a --filter name=simples-exec

# Confirmar que os serviços principais estão rodando
docker compose ps

# Verificar saúde do backend
curl -f http://localhost/api/health

# Verificar métricas
curl http://127.0.0.1:9090/metrics | Select-String 'executions_total\|rate_limits_total'
```

## Prevention Summary

| Incidente | Prevenção | Mitigação |
|---|---|---|
| Loop Infinito | `EXEC_TIMEOUT_S=10` + SIGTERM/SIGKILL | Logs de timeout, remoção automática do container |
| Exploit | Docker sandbox (cap_drop, read-only, no-network) | `security_tests.py` valida as regras |
| Acesso à Rede | `network_mode='none'` + remoção de capabilities | Logs de erro de socket |
| DoS | Rate limiting + cgroups (mem/cpu) | Reinício do backend, verificação de métricas |
| Containers Órfãos | `auto_remove=True` + cleanup pós-execução | `docker rm` manual, `docker system prune` |

> **Nota:** Em caso de incidente de segurança confirmado (exploit bemsucedido ou vazamento de dados), o admin deve desligar os serviços imediatamente com `docker compose down` e notificar os responsáveis pela disciplina.
