# Multi-stage build para otimizar tamanho final
FROM node:18-alpine as builder

WORKDIR /app

# Copiar package.json e package-lock.json
COPY frontend/package*.json ./

# Instalar dependências
RUN npm ci

# Copiar código-fonte
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html ./
COPY frontend/vite.config.js ./
COPY frontend/tsconfig.json ./

# Build
RUN npm run build

# Stage final - servidor de desenvolvimento (durante desenvolvimento)
FROM node:18-alpine

WORKDIR /app

# Instalar serve para servir arquivos estáticos
RUN npm install -g serve

# Copiar node_modules e código do builder
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/package*.json ./
COPY frontend/index.html ./
COPY frontend/vite.config.js ./

# Expor porta de desenvolvimento
EXPOSE 5173

# Comando: rodar dev server (para desenvolvimento)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
