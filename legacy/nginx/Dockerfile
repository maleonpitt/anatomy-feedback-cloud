# ============================================
# Stage 1: NGINX Production Server (LEGACY)
# ============================================
FROM nginx:alpine

# Copy custom Nginx config (archived — not target architecture)
COPY legacy/nginx/default.conf /etc/nginx/conf.d/default.conf

# Clean out the default Nginx web root
RUN rm -rf /usr/share/nginx/html/*

# SSL certificates will be mounted at runtime via docker-compose:
#   - /etc/letsencrypt/live/app.heilab.pitt.edu/
#   - /etc/letsencrypt/options-ssl-nginx.conf
#   - /etc/letsencrypt/ssl-dhparams.pem
# (Do NOT copy them into the image — they should remain on the host)

# Ensure proper permissions (optional safety)
RUN mkdir -p /etc/letsencrypt && chmod -R 755 /etc/letsencrypt

# Expose both HTTP and HTTPS ports
EXPOSE 80 443

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
