# Roadmap sugerido

## Fase 0 — Descubrimiento (1-2 semanas)

- Definir alcance del MVP por perfil de ISP.
- Elegir stack y criterios de despliegue.
- Definir proveedor de WhatsApp y estrategia de plantillas.
- Acordar si el bot arranca solo con n8n o con n8n + OpenAI.

## Fase 1 — Core CRM + Billing (3-5 semanas)

- Multi-tenant, RBAC y branding base.
- Clientes, planes, servicios y contratos.
- Facturas, pagos y estado de cuenta.
- Reglas de mora y política de suspensión.

## Fase 2 — Integraciones de red (3-4 semanas)

- Conector MikroTik para corte/reconexión + sincronización inicial.
- Conector UISP para inventario y estado operativo.
- Auditoría técnica por comando y visualización en panel.

## Fase 3 — WhatsApp Inbox + Automatización (3-4 semanas)

- Inbox WhatsApp con asignación y etiquetas.
- Eventos de negocio hacia n8n.
- Flujos automáticos de cobranza (recordatorio, aviso, corte, reconexión).
- SLA básico y trazabilidad de atención.

## Fase 4 — Chatbot n8n/OpenAI + Operación asistida (2-4 semanas)

- Bot para preguntas de facturas, pagos y estado de servicio.
- Clasificación de intención y respuestas sugeridas para agentes.
- Escalamiento automático a humano en casos críticos.
- Control de costo y calidad del bot por tenant.

## Fase 5 — Marca blanca avanzada + Escala (2-4 semanas)

- Dominios por tenant.
- Planes de subarrendamiento y límites operativos.
- Métricas por tenant (operación, cobranza, atención).

## KPIs recomendados

- DSO (días de cobro promedio).
- % de corte/reconexión automáticos exitosos.
- % de resolución por bot sin agente.
- Tiempo promedio de primera respuesta en WhatsApp.
- Disponibilidad de conectores MikroTik/UISP.
