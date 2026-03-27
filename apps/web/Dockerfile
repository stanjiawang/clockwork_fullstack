FROM node:22-alpine AS build

WORKDIR /workspace

ARG VITE_BFF_HTTP_URL=http://localhost:8000
ARG VITE_BFF_STREAM_URL=ws://localhost:8000/api/stream

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/contracts/package.json packages/contracts/package.json

RUN pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY packages/contracts packages/contracts

ENV VITE_BFF_HTTP_URL=$VITE_BFF_HTTP_URL
ENV VITE_BFF_STREAM_URL=$VITE_BFF_STREAM_URL

RUN pnpm --dir apps/web build

FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/web/dist /usr/share/nginx/html

EXPOSE 8080
