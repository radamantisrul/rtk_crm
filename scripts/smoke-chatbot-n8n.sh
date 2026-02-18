#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${WEBHOOK_URL:-}" ]]; then
  echo "ERROR: define WEBHOOK_URL, por ejemplo:"
  echo 'WEBHOOK_URL="http://localhost:5678/webhook-test/crm-events" ./scripts/smoke-chatbot-n8n.sh'
  exit 1
fi

echo "Simulando mensaje entrante de WhatsApp para chatbot..."

curl -sS -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-demo",
    "tipo_evento": "whatsapp.message.received",
    "cliente_id": "C-1001",
    "telefono": "+529991112233",
    "mensaje": "hola, ya pagué, me ayudas a reconectar?",
    "timestamp": "2026-02-18T12:00:00Z"
  }'

echo

echo "OK: smoke de chatbot enviado."
