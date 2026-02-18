# Diseño del chatbot (n8n + OpenAI)

## Objetivo
Automatizar **cobranza y atención al cliente** por WhatsApp sin perder control operativo.

## Opción A: Chatbot 100% n8n (sin LLM)

Útil para MVP rápido y bajo costo:

- Reglas basadas en palabras clave y estados del CRM.
- Plantillas para:
  - saldo pendiente,
  - fecha de vencimiento,
  - confirmación de pago,
  - estado de servicio.
- Escalamiento a agente cuando no hay coincidencia.

## Opción B: n8n + OpenAI (recomendada)

n8n orquesta flujos y OpenAI aporta comprensión de lenguaje natural:

1. Mensaje entra por webhook de WhatsApp.
2. n8n consulta CRM (cliente, facturas, estado de servicio).
3. OpenAI clasifica intención y redacta respuesta.
4. n8n aplica reglas de negocio (por ejemplo, no prometer reconexión si no hay pago confirmado).
5. Se responde por WhatsApp o se escala a humano.

## Intenciones mínimas

- `consulta_saldo`
- `consulta_vencimiento`
- `confirmar_pago`
- `estado_servicio`
- `reportar_falla`
- `hablar_con_agente`

## Reglas de seguridad del bot

- Nunca exponer datos de otro cliente.
- Validar identidad mínima (teléfono + dato de control).
- Registrar cada interacción para auditoría.
- Bloquear acciones destructivas sin validación (p. ej. cambio de plan).

## Automatización de pagos sugerida

- Día -3 al vencimiento: recordatorio amable.
- Día 0: aviso de vencimiento.
- Día +X: aviso previo a suspensión.
- Día +Y: suspensión automática (según política del tenant).
- Al registrar pago: reconexión + mensaje de confirmación.

## KPIs específicos del bot

- % de conversaciones resueltas automáticamente.
- Tiempo promedio de resolución por intención.
- % de escalamiento a humano.
- Costo estimado por conversación (si usa OpenAI).
