#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <ssh-user> <host> <remote-dir> [ssh-port]" >&2
  echo "Example: $0 ubuntu demo.example.com /opt/clockwork 22" >&2
  exit 1
fi

SSH_USER="$1"
HOST="$2"
REMOTE_DIR="$3"
SSH_PORT="${4:-22}"

FILES=(
  "${ROOT_DIR}/Caddyfile"
  "${ROOT_DIR}/docker-compose.vm.yml"
  "${ROOT_DIR}/deploy-vm.sh"
  "${ROOT_DIR}/vm.env.example"
)

for file in "${FILES[@]}"; do
  if [[ ! -f "${file}" ]]; then
    echo "Missing required file: ${file}" >&2
    exit 1
  fi
done

ssh -p "${SSH_PORT}" "${SSH_USER}@${HOST}" "mkdir -p '${REMOTE_DIR}'"
scp -P "${SSH_PORT}" "${FILES[@]}" "${SSH_USER}@${HOST}:${REMOTE_DIR}/"

cat <<EOF
Bundle copied to ${SSH_USER}@${HOST}:${REMOTE_DIR}

Next commands on the VM:

  cd ${REMOTE_DIR}
  cp vm.env.example .env
  nano .env
  chmod +x deploy-vm.sh
  ./deploy-vm.sh

If Docker is not installed yet, run bootstrap first as root:

  sudo bash ${REMOTE_DIR}/bootstrap-oracle-vm.sh
EOF
