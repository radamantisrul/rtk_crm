# CRM ISP Marca Blanca (MikroTik + UISP + n8n + WhatsApp)

Este proyecto define un **CRM para proveedores de internet (WISP/ISP)**, pensado para operar como plataforma **multi-tenant de marca blanca** (subarrendable).

## Visión del producto
Construir una alternativa estilo WispHub que una en un solo sistema:

- Operación comercial (clientes, planes, contratos, facturación y cobranza).
- Operación técnica (monitoreo MikroTik y UISP).
- Operación de atención (bandeja WhatsApp tipo Chatwoot).
- Automatización con **n8n** y un **chatbot con n8n u OpenAI**.

## Alcance MVP

1. **Estado de cuenta y cobranza**
   - Cargos mensuales, saldo, pagos, vencimiento y mora.
   - Reglas de suspensión/reconexión automática por políticas del tenant.

2. **Activar/desactivar servicios desde CRM**
   - MikroTik: corte/reconexión por RouterOS API.
   - UISP/EdgeRouter: sincronización de servicio y estado operativo.

3. **Monitoreo de red**
   - Estado online/offline de CPE y enlace.
   - Métricas: señal, CCQ, latencia, jitter, throughput, disponibilidad.

4. **Bandeja de WhatsApp**
   - Conversaciones por cliente con historial, etiquetas y asignación.
   - Vista unificada para soporte/cobranza.

5. **Chatbot y automatizaciones (n8n + OpenAI opcional)**
   - Flujos automáticos de cobranza y seguimiento de tickets.
   - Bot con respuestas sobre estado de cuenta, estado del servicio y FAQs.
   - Escalamiento a agente humano cuando corresponda.

6. **Marca blanca multi-tenant**
   - Branding por tenant: logo, colores, dominio.
   - Aislamiento de datos por `tenant_id`.

## Documentación

- [Arquitectura propuesta](docs/arquitectura.md)
- [Modelo de datos inicial](docs/modelo-datos.md)
- [Diseño de chatbot (n8n + OpenAI)](docs/chatbot-n8n-openai.md)
- [Roadmap por fases](docs/roadmap.md)

## Propuesta de stack inicial

- Backend API: NestJS/Node.js
- DB transaccional: PostgreSQL
- Cola y caché: Redis + BullMQ
- Frontend: React + Next.js
- Integraciones: microservicios workers (MikroTik, UISP, WhatsApp)
- Automatización: n8n (self-hosted)

## Próximos pasos sugeridos

1. Definir el primer vertical: **cobranza + corte/reconexión automática**.
2. Implementar modelo de tenants y RBAC.
3. Entregar módulo de facturación/estado de cuenta.
4. Integrar MikroTik y UISP con trazabilidad y auditoría.
5. Activar flujos de WhatsApp + n8n + bot (n8n/OpenAI).


## Cómo probar ahora mismo

Sigue la guía rápida en [`docs/como-probar.md`](docs/como-probar.md) y ejecuta los smoke tests con scripts en `scripts/`.
