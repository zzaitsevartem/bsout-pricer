# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Рантайм — standalone.
# В next.config.mjs выставлен `output: 'standalone'`, поэтому сборка кладёт в
# .next/standalone самодостаточный сервер с минимальным node_modules и
# server.js. В финальный образ копируются только .next/standalone,
# .next/static и public — стадия prod-deps с полным `npm ci --omit=dev`
# больше не нужна (образ меньше примерно втрое против `next start`).
#
# ВАЖНО про BACKEND_URL: вместе со standalone rewrites из next.config.mjs
# вычисляются на СБОРКЕ и попадают в .next/routes-manifest.json. Поэтому
# BACKEND_URL передаётся сюда как build-arg, иначе в манифест запечётся
# дефолт http://localhost:8000. Прод задаёт его в docker-compose.prod.yml
# (build.args у сервиса frontend).
#
# В проде этот рерайт — запасной путь: nginx перехватывает /api/ сам
# (location ^~ /api/ в deploy/nginx/bscout.conf) и проксирует напрямую
# в backend, минуя Next.
# ---------------------------------------------------------------------------

# --- Зависимости для сборки -------------------------------------------------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# --- Сборка Next.js --------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=${BACKEND_URL}
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

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD wget -q -O /dev/null "http://127.0.0.1:${PORT}/" || exit 1

CMD ["node", "server.js"]
