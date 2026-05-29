FROM nginx:alpine

# Remover configuração padrão
RUN rm /etc/nginx/conf.d/default.conf

# Copiar configuração customizada
COPY docker/nginx.conf /etc/nginx/conf.d/

# Expor porta 80
EXPOSE 80

# Nginx em foreground
CMD ["nginx", "-g", "daemon off;"]
