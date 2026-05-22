FROM node:22-bookworm-slim AS builder

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
ARG VITE_SERVER_API_URL=http://localhost:8002
ARG VITE_SERVER_API_PREFIX=/api/v1
ARG VITE_SERVER_API_TIMEOUT=5000
ENV VITE_SERVER_API_URL=$VITE_SERVER_API_URL
ENV VITE_SERVER_API_PREFIX=$VITE_SERVER_API_PREFIX
ENV VITE_SERVER_API_TIMEOUT=$VITE_SERVER_API_TIMEOUT
RUN pnpm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
