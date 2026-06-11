# Stage 1: Build simplesc compiler from source
FROM ubuntu:24.04 AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy simples-compiler source
COPY simples-compiler/ ./simples-compiler/

# Build simplesc
RUN cd simples-compiler && \
    make clean && \
    make && \
    cp simplesc /usr/local/bin/simplesc && \
    simplesc --help 2>&1 || true

# Stage 2: Python runtime with toolchain
FROM python:3.11-slim

WORKDIR /app

# Install compilation toolchain and runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    nasm \
    binutils-i686-linux-gnu \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy simplesc binary from builder stage
COPY --from=builder /usr/local/bin/simplesc /usr/local/bin/simplesc

# Copy Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/src ./src
COPY backend/tests ./tests

# Copy example SIMPLES programs
COPY simples-compiler/examples ./examples

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Verify toolchain
RUN simplesc --help 2>&1 || true && \
    nasm -v && \
    i686-linux-gnu-ld --version

# Command to run Flask
CMD ["flask", "run", "--host", "0.0.0.0"]
