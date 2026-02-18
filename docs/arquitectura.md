# Arquitectura propuesta

## 1) Arquitectura de alto nivel

Diseño modular con API central y workers especializados:

- **Core CRM API**: autenticación, RBAC, multitenancy, clientes y servicios.
- **Billing Service**: facturas, pagos, mora, reglas de corte/reconexión.
- **Network Integrations**:
  - Connector MikroTik (RouterOS API)
  - Connector UISP
  - Connector EdgeRouter (cuando aplique)
- **Messaging Hub**: integración WhatsApp + inbox de conversaciones.
- **Automation Bridge (n8n)**: webhooks/eventos de negocio + acciones de retorno.
- **AI Orchestrator (opcional OpenAI)**: capa de IA para clasificación, respuesta y resumen.
- **Monitoring Pipeline**: ingestión por polling/webhooks, cálculo de salud y alertas.
- **Frontend Web**: panel comercial/técnico por tenant.

## 2) Multi-tenant de marca blanca

Aislamiento estricto por `tenant_id` en datos y permisos:

- Branding por tenant: logo, colores, templates y dominio.
- Configuración por tenant: políticas de suspensión, SLA y horarios.
- Planes de subarrendamiento: límites por usuarios/clientes/dispositivos.

## 3) Integración MikroTik

### Capacidades del MVP
- Sincronización de clientes/servicios (PPPoE Secrets o DHCP leases).
- Corte y reconexión por estado de pago.
- Lectura de uptime, consumo y última conexión.

### Patrón recomendado
- Workers asincrónicos por cola (evitar bloqueos del API).
- Reintentos idempotentes y DLQ para fallos repetidos.
- Bitácora de auditoría por comando ejecutado.

## 4) Integración UISP

### Capacidades del MVP
- Sincronizar sitios, CPE, enlaces y estado.
- Obtener RSSI/CCQ/latencia/throughput/disponibilidad.
- Asociar dispositivo y enlace al servicio del cliente.

## 5) WhatsApp tipo Chatwoot

### Capacidades mínimas
- Ingreso/salida de mensajes por webhook API.
- Conversación por cliente y canal.
- Estados: abierta, pendiente, resuelta.
- Asignación a agente o cola.

### Estrategia de entrega
- Fase rápida: integrar Chatwoot por API.
- Fase avanzada: inbox propio en CRM.

## 6) n8n + OpenAI para chatbot y automatización

### Eventos publicados a n8n
- `invoice.created`
- `invoice.overdue`
- `payment.received`
- `service.suspended`
- `service.reconnected`
- `whatsapp.message.received`
- `ticket.created`

### Acciones que n8n puede ejecutar en CRM
- Enviar WhatsApp.
- Crear/actualizar tarea de cobranza.
- Suspender/reconectar servicio.
- Crear ticket y asignar a soporte.

### Rol de OpenAI (opcional)
- Clasificar intención del mensaje (cobranza, soporte, ventas).
- Responder FAQs y consultas de estado de cuenta/servicio.
- Resumir conversaciones para agentes.
- Detectar casos de escalamiento.

## 7) Flujo crítico de cobranza automática

1. Billing detecta factura vencida.
2. Publica evento `invoice.overdue` al Automation Bridge.
3. n8n ejecuta recordatorio WhatsApp con plantilla.
4. Si no hay pago en ventana definida, n8n solicita suspensión.
5. Network connector ejecuta corte (MikroTik/UISP) y audita resultado.
6. Al registrar pago (`payment.received`), n8n dispara reconexión.

## 8) Seguridad

- RBAC por tenant y trazabilidad de acciones.
- Cifrado de credenciales de integración en repositorio seguro.
- Firma/verificación de webhooks de entrada/salida.
- Rate limit por tenant y por integración externa.
