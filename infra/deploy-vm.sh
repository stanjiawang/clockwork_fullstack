#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.vm.yml"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy infra/vm.env.example to infra/.env and update it." >&2
  exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "Missing ${COMPOSE_FILE}" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed on this host." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is not available on this host." >&2
  exit 1
fi

echo "Logging in to GHCR."
read -rp "GitHub username: " GHCR_USERNAME
echo -n "GitHub token (read:packages): "
read -rs GHCR_TOKEN
echo

echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin

echo "Pulling images."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" pull

echo "Starting stack."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d

echo "Current status."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

APP_DOMAIN="$(grep '^APP_DOMAIN=' "${ENV_FILE}" | cut -d'=' -f2- || true)"
if [[ -n "${APP_DOMAIN}" ]]; then
  echo "Smoke checks:"
  echo "  https://${APP_DOMAIN}/healthz"
  echo "  https://${APP_DOMAIN}/api/health"
  echo "  https://${APP_DOMAIN}/api/scenario"
  echo "  https://${APP_DOMAIN}/api/topology"
fi
