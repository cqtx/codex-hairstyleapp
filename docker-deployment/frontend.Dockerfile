# Build the Angular application
FROM node:20-alpine AS build
WORKDIR /app
COPY source/frontend/package*.json ./
RUN npm ci
COPY source/frontend/ ./
RUN npm run build -- --configuration production

# Serve the compiled assets with Nginx
FROM nginx:1.25-alpine
COPY docker-deployment/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/hairstyle-app /usr/share/nginx/html
EXPOSE 80
