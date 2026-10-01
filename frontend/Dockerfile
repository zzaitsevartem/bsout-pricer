# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# ВНИМАНИЕ про standalone.
# В next.config.mjs НЕ выставлен `output: 'standalone'`, поэтому собрать
# минимальный self-contained образ (.next/standalone + server.js) нельзя:
# рантайм-стадия тащит production-зависимости и запускает `next start`.
# Как только в next.config.mjs появится `output: 'standalone'`, рантайм можно
# ужать до COPY .next/standalone + .next/static + public (образ меньше ~в 3 раза).
# next.config.mjs — не файл этой задачи, см. needs_shared_change.
# ---------------------------------------------------------------------------

# --- Зависимости для сборки (dev + prod) -----------------------------------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# --- Только production-зависимости для финального образа --------------------
FROM node:20-alpine AS prod-deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund

# --- Сборка Next.js --------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- Рантайм ---------------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Непривилегированный пользователь: node-процесс не должен быть root.
# Флаги короткие — в alpine это busybox adduser, длинных опций он не понимает.
RUN addgroup -g 10001 -S nodejs \
    && adduser -u 10001 -S -G nodejs nextjs

COPY --from=prod-deps --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder   --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder   --chown=nextjs:nodejs /app/public ./public
COPY --from=builder   --chown=nextjs:nodejs /app/package.json ./package.json
# next.config.mjs читается и на рантайме: в нём живёт rewrite /api/* -> BACKEND_URL
COPY --from=builder   --chown=nextjs:nodejs /app/next.config.mjs ./next.config.mjs

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD wget -q -O /dev/null "http://127.0.0.1:${PORT}/" || exit 1

CMD ["node_modules/.bin/next", "start"]
