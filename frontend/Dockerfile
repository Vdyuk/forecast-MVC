# === Stage 1: Сборка приложения ===
FROM node:18 AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Собираем через прямой вызов Vite через Node
RUN node node_modules/vite/bin/vite.js build

# === Stage 2: Сервинг статики через nginx ===
FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf
RUN rm -rf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]