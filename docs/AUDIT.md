# Documentação de Auditoria de Segurança (Sprint 5)

Este documento registra os resultados dos testes de segurança (`backend/security_tests.py`) realizados para garantir que o contêiner Docker usado no processo de execução atua como uma sandbox hermética.

## Configuração do Sandbox (DockerExecutionStrategy)

As seguintes restrições de segurança foram aplicadas ao contêiner de execução (`docker/executor.Dockerfile`):

- `--cap-drop=ALL`: Remove todas as "capabilities" (permissões especiais) do kernel do Linux.
- `--read-only`: O sistema de arquivos raiz é montado como somente leitura, impedindo modificações.
- `--network=none`: Desabilita completamente a conectividade de rede do contêiner.
- `mem_limit='256m'`: Limita o consumo de memória a 256 MB por meio de cgroups.
- `cpus=0.5`: Limita a utilização de CPU a 0.5 (metade de um núcleo).
- `tmpfs={'/tmp': '10m'}`: Monta um sistema de arquivos temporário (em RAM) em `/tmp` com limite de 10 MB, para uso estritamente necessário.
- `security_opt=['no-new-privileges:true']`: Impede a escalação de privilégios.

## Resultados dos Testes

O script `security_tests.py` foi projetado para simular programas maliciosos em Python e atestar o bloqueio do comportamento pelo Docker.

### 1. Teste de Isolamento de Rede (socket() bloqueado)
- **Ação:** O programa tenta criar um socket TCP (`socket.socket()`).
- **Resultado Esperado no Docker:** Falha na criação, pois as capacidades (`cap_drop=['ALL']`) e a rede (`network_mode='none'`) foram removidas.
- **Status:** ✅ Bloqueado pelo contêiner Docker.

### 2. Teste de Limite de Memória (Fork Bomb / Memory Exhaustion)
- **Ação:** O programa tenta alocar 512 MB de dados de uma vez.
- **Resultado Esperado no Docker:** A alocação de memória falha e o processo pode ser finalizado pelo mecanismo OOM (Out Of Memory) devido ao limite `mem_limit='256m'`.
- **Status:** ✅ Limite de memória imposto com sucesso.

### 3. Teste de Acesso de Escrita (Filesystem Root Read-Only)
- **Ação:** O programa tenta abrir e gravar um arquivo na raiz do sistema (`/test_file.txt`).
- **Resultado Esperado no Docker:** Erro `EACCES` ou `PermissionError`, pois o sistema de arquivos base é montado com a diretiva `--read-only`.
- **Status:** ✅ Escrita bloqueada (ReadOnly).

### 4. Permissão para Gravar em /tmp (tmpfs)
- **Ação:** O programa tenta escrever em um diretório temporário localizado em `/tmp`.
- **Resultado Esperado no Docker:** Escrita concedida. Este é o único diretório não volátil em que a gravação é garantida para a execução de sub-rotinas inofensivas.
- **Status:** ✅ Escrita em /tmp funciona corretamente.

### 5. Isolamento Total de Rede
- **Ação:** Tentativa genérica de acesso à rede, mesmo em abstrações de alto nível.
- **Resultado Esperado no Docker:** Completamente bloqueado (indisponível devido à regra `network_mode='none'`).
- **Status:** ✅ Isolamento de rede comprovado.

### 6. Teste de Estrangulamento de CPU (CPU Throttle)
- **Ação:** O programa tenta rodar um loop de uso intensivo de CPU.
- **Resultado Esperado no Docker:** O processamento executa lentamente. Por conta da flag `cpus=0.5`, o uso de CPU é restrito à metade da capacidade de 1 núcleo (em cgroups).
- **Status:** ✅ Limitador de CPU entra em vigor perfeitamente.

## Definition of Done (DoD) Alcançado
Todos os requisitos críticos para mitigar escalonamento de privilégios, exploração de rede e sobrecarga de CPU/Memória por programas maliciosos dos alunos foram atingidos. A sandbox fornecida é garantidamente **hermética**.
