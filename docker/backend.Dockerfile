FROM ubuntu:24.04 AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    make \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/pm-avila/simples-compiler /tmp/compiler && \
    cd /tmp/compiler && \
    make && \
    cp build/simplesc /usr/local/bin/simplesc && \
    rm -rf /tmp/compiler

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    nasm \
    binutils-i686-linux-gnu \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/bin/simplesc /usr/local/bin/simplesc

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src ./src
COPY backend/tests ./tests

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

RUN simplesc --version 2>&1 || true && \
    nasm -v && \
    i686-linux-gnu-ld --version

CMD ["flask", "run", "--host", "0.0.0.0"]
