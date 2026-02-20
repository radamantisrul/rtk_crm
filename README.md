# RTK CRM (MVP)

CRM multi-compañía inspirado en Chatwoot + WispHub, con base para operación ISP:

- Multi-tenant (cada compañía con su propia configuración y red lógica).
- Integraciones por compañía: UISP, OpenAI, n8n y Google.
- Gestión de clientes con activación/suspensión sincronizable a UISP.
- Automatizaciones por eventos (ej. cambio de estado) con disparo a webhook de n8n.
- Modelo de sub-arriendo (reseller): una compañía puede tener compañías hijas.
- Interfaz web amigable para operaciones básicas en `/`.

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

Abre `http://localhost:8000` para la interfaz web.

## Ejecutar tests

```bash
pytest
```

## Endpoints clave

- `GET /` (UI)
- `POST /companies`
- `GET /companies`
- `POST /companies/{company_id}/integrations`
- `POST /companies/{company_id}/automations`
- `POST /companies/{company_id}/customers`
- `POST /companies/{company_id}/customers/{customer_id}/status`
- `GET /companies/{company_id}/dashboard`

> Este MVP prioriza la arquitectura base y los flujos críticos de negocio.
