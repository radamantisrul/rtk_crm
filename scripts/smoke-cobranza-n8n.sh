#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${WEBHOOK_URL:-}" ]]; then
  echo "ERROR: define WEBHOOK_URL, por ejemplo:"
  echo 'WEBHOOK_URL="http://localhost:5678/webhook-test/crm-events" ./scripts/smoke-cobranza-n8n.sh'
  exit 1
fi

send_event() {
  local payload="$1"
  echo "--> POST $WEBHOOK_URL"
  curl -sS -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$payload"
  echo
  echo
}

echo "[1/2] Simulando factura vencida (invoice.overdue)"
send_event '{
  "tenant_id": "tenant-demo",
  "tipo_evento": "invoice.overdue",
  "cliente_id": "C-1001",
  "factura": {
    "id": "F-2026-00045",
    "saldo": 650.00,
    "fecha_vencimiento": "2026-02-15"
  },
  "canal_preferido": "whatsapp"
}'

echo "[2/2] Simulando pago recibido (payment.received)"
send_event '{
  "tenant_id": "tenant-demo",
  "tipo_evento": "payment.received",
  "cliente_id": "C-1001",
  "pago": {
    "id": "P-987",
    "monto": 650.00,
    "referencia": "TRX-ABC-123"
  },
  "accion_esperada": "reconnect_service"
}'

echo "OK: smoke de cobranza enviado."
