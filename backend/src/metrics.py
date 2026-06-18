from prometheus_client import Counter, Histogram

# Compilations
COMPILATIONS = Counter(
    'simples_compilations_total',
    'Total number of compilations',
    ['status'] # 'success', 'error'
)

# Executions
EXECUTIONS = Counter(
    'simples_executions_total',
    'Total number of executions',
    ['status'] # 'success', 'timeout', 'stop', 'error'
)

# Request Latency
LATENCY = Histogram(
    'simples_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    # Buckets em segundos otimizados para requisições rápidas e lentas (incluindo timeouts de 10s-15s)
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, float("inf"))
)

# Rate Limiting
RATE_LIMITS = Counter(
    'simples_rate_limit_rejections_total',
    'Total number of rate limit rejections'
)
