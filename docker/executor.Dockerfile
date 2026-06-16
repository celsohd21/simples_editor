# Minimal executor image for hardened execution
# Used by DockerExecutionStrategy for running compiled SIMPLES programs

FROM alpine:3.18

# Install only libc (needed by compiled i686 programs)
RUN apk add --no-cache musl-dev glibc-dev libc6-compat

# Create app directory
WORKDIR /app

# Create /tmp directory with proper permissions
RUN mkdir -p /tmp && chmod 1777 /tmp

# Default command (will be overridden)
CMD ["/app/program"]

# Labels for documentation
LABEL maintainer="Simples Editor"
LABEL description="Minimal sandbox for executing compiled SIMPLES programs"
LABEL security.hardening="cap_drop=ALL,read_only=true,network=none,memory_limit=256m,cpu_limit=0.5"
