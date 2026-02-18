# Cómo probar el diseño (rápido y sin backend completo)

Si aún no tienes el CRM implementado, puedes **probar la automatización de cobranza y chatbot** usando n8n + webhooks.

## 1) Levantar n8n local

```bash
docker run --name n8n-test -p 5678:5678 -e N8N_SECURE_COOKIE=false -it n8nio/n8n
```

Cuando inicie, abre:
- http://localhost:5678

## 2) Crear un workflow mínimo en n8n

Crea un workflow con estos nodos:

1. **Webhook** (POST)
   - Path: `crm-events`
2. **Switch** sobre `{{$json.tipo_evento}}`
   - Caso `invoice.overdue`
   - Caso `payment.received`
   - Caso `whatsapp.message.received`
3. **Respond to Webhook**
   - Respuesta JSON indicando qué rama tomó.

> Tip: puedes empezar con un solo Webhook + Respond to Webhook para validar que recibes payload.

## 3) Activar el webhook de prueba

En n8n, abre el nodo Webhook y copia su URL de prueba, por ejemplo:

- `http://localhost:5678/webhook-test/crm-events`

## 4) Ejecutar smoke tests

Desde este repo:

```bash
chmod +x scripts/smoke-cobranza-n8n.sh scripts/smoke-chatbot-n8n.sh
WEBHOOK_URL="http://localhost:5678/webhook-test/crm-events" ./scripts/smoke-cobranza-n8n.sh
WEBHOOK_URL="http://localhost:5678/webhook-test/crm-events" ./scripts/smoke-chatbot-n8n.sh
```

## 5) Qué deberías ver

- En n8n: ejecuciones entrantes con `tipo_evento` diferente.
- En la terminal: respuestas HTTP 200 con JSON del workflow.
- En los logs: eventos de ejemplo para cobranza y atención.

## 6) Prueba opcional con OpenAI (más adelante)

Cuando conectes OpenAI en n8n:

- En la rama `whatsapp.message.received`, agrega nodo LLM.
- Usa intención mínima:
  - `consulta_saldo`
  - `consulta_vencimiento`
  - `confirmar_pago`
  - `estado_servicio`
  - `hablar_con_agente`
- Mantén una regla dura: **siempre validar estado real en CRM antes de prometer reconexión**.

## 7) Checklist de “ya quedó probado”

- [ ] Recibo `invoice.overdue` en n8n.
- [ ] Recibo `payment.received` en n8n.
- [ ] Recibo `whatsapp.message.received` en n8n.
- [ ] El workflow enruta correctamente por tipo de evento.
- [ ] Se puede responder al cliente con mensaje de prueba.

