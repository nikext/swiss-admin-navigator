# Web UI + BFF for Cloud Run (M6, docs/GCP.md §4). Build from web/:
#   docker build -t swiss-nav-web web
# Next.js "standalone" output: a self-contained server.js plus only the
# node_modules it traces, so the runtime image carries no dev dependencies.

FROM node:22.23.2-bookworm-slim@sha256:48e4b67d85f87bd551df43704e24d252f56cc5f8e9718841aace50f19948f0f9 AS build
WORKDIR /src
ENV NEXT_TELEMETRY_DISABLED=1
# npm 10 (bundled with Node 22) can't build this lockfile's optional peer set
# ("Cannot read properties of null (reading 'edgesOut')"); the lock comes from npm 11.
RUN npm install -g npm@11.6.2 --no-fund --no-audit
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22.23.2-bookworm-slim@sha256:48e4b67d85f87bd551df43704e24d252f56cc5f8e9718841aace50f19948f0f9
LABEL org.opencontainers.image.source="https://github.com/nikext/swiss-admin-navigator" \
      org.opencontainers.image.description="Unofficial Swiss Admin Navigator web UI. Not legal advice." \
      org.opencontainers.image.licenses="Apache-2.0"
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=8080
COPY --from=build --chown=node:node /src/.next/standalone ./
COPY --from=build --chown=node:node /src/.next/static ./.next/static
USER node
EXPOSE 8080
CMD ["node", "server.js"]
