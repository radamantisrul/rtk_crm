# Modelo de datos inicial (MVP)

## Entidades base

## Tenant
- id
- nombre
- dominio
- logo_url
- color_primario
- estado
- configuracion_json

## Usuario
- id
- tenant_id
- nombre
- email
- rol (admin, soporte, cobranza, operador)
- estado

## Cliente
- id
- tenant_id
- codigo_cliente
- nombre_razon_social
- documento
- telefono
- email
- direccion
- estado_servicio (activo, suspendido, baja)

## PlanServicio
- id
- tenant_id
- nombre
- velocidad_bajada_mbps
- velocidad_subida_mbps
- precio_mensual
- impuestos
- politica_suspension

## Servicio
- id
- tenant_id
- cliente_id
- plan_id
- tecnologia (pppoe, dhcp, fiber, wireless)
- dispositivo_ref
- fecha_activacion
- fecha_corte
- estado

## Factura
- id
- tenant_id
- cliente_id
- servicio_id
- periodo
- monto_total
- saldo
- fecha_emision
- fecha_vencimiento
- estado (pendiente, pagada, vencida)

## Pago
- id
- tenant_id
- cliente_id
- factura_id
- monto
- metodo (efectivo, transferencia, pasarela)
- referencia
- fecha_pago
- estado_conciliacion

## DispositivoRed
- id
- tenant_id
- proveedor (mikrotik, uisp)
- external_id
- nombre
- ip_gestion
- estado
- metricas_json
- ultimo_sync_at

## Conversacion
- id
- tenant_id
- cliente_id
- canal (whatsapp)
- estado (abierta, pendiente, resuelta)
- asignado_a
- ultimo_mensaje_at

## Mensaje
- id
- tenant_id
- conversacion_id
- tipo (entrante, saliente)
- contenido
- metadata_json
- fecha

## EventoIntegracion
- id
- tenant_id
- origen (mikrotik, uisp, whatsapp, n8n, openai)
- tipo_evento
- payload_json
- procesado
- fecha

## AutomatizacionFlujo
- id
- tenant_id
- nombre
- proveedor (n8n)
- webhook_url
- activo

## AIInteraction
- id
- tenant_id
- cliente_id
- conversacion_id
- proveedor (openai)
- prompt_tokens
- completion_tokens
- costo_estimado
- clasificacion_intencion
- escalado_humano
- fecha

## Relaciones críticas

- Tenant 1:N Usuarios, Clientes, Planes, Servicios, Facturas, Flujos y Conversaciones.
- Cliente 1:N Servicios, Facturas, Pagos y Conversaciones.
- Conversación 1:N Mensajes y 1:N AIInteraction.
- Servicio 1:1 o 1:N DispositivoRed (según topología).
- Factura 1:N Pagos.
