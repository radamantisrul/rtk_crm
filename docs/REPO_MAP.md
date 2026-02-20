# REPO MAP — Estado actual

## 1) Estructura de carpetas

```text
.
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── services.py
│   ├── static/
│   │   ├── app.js
│   │   └── styles.css
│   └── templates/
│       └── index.html
├── web/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── nginx/
│   ├── frontend.conf
│   └── vps.conf
├── tests/
│   └── test_api.py
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 2) Cómo se corre hoy (comandos)

### API (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

API local: `http://localhost:8000`.

### Frontend (React + Vite)

```bash
cd web
cp .env.example .env
npm install
npm run dev
```

Frontend local: `http://localhost:5173`.

### Opción compose (dev)

```bash
docker compose up --build
```

## 3) Cómo se build hoy

### Build backend
No hay paso de bundle como tal; el backend se instala con packaging Python:

```bash
pip install -e .
```

### Build frontend

```bash
cd web
npm install
npm run build
```

Salida: `web/dist/`.

## 4) Dónde está el backend y cómo conecta

- Backend principal: `app/main.py` (FastAPI).
- Modelos/contratos: `app/schemas.py`.
- Lógica de negocio en memoria: `app/services.py`.
- Endpoints de negocio: `/companies`, `/companies/{id}/customers`, `/companies/{id}/dashboard`, etc.
- Health público: `/health`.

Conexión con frontend:
- La SPA en `web/` consume el backend por HTTP usando `fetch` centralizado en `web/src/api.js`.
- `API_BASE_URL` se compone desde variable `VITE_API_BASE_URL`.

## 5) Dónde se configura base URL y API key

### Frontend
- `web/.env` (a partir de `.env.example`):
  - `VITE_API_BASE_URL`
  - `VITE_API_KEY` (opcional)
- Uso en código: `web/src/api.js`.

### Backend
- `RTK_API_KEY` en variables de entorno del proceso FastAPI.
- Si existe, `app/main.py` exige header `x-api-key` en endpoints de negocio.
- `/health` no requiere key.

## 6) Cómo se despliega hoy en VPS (pasos actuales)

1. Clonar repo en VPS.
2. Crear venv e instalar backend:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
3. Configurar `RTK_API_KEY` (opcional/recomendado).
4. Ejecutar API en loopback:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
5. Build del frontend:
   ```bash
   cd web
   npm install
   VITE_API_BASE_URL=/api npm run build
   ```
6. Publicar `web/dist` en `/var/www/rtk-crm-web`.
7. Configurar Nginx con `nginx/vps.conf`:
   - `/api/` → proxy a `127.0.0.1:8000`
   - `/` → servir SPA estática
8. Recargar Nginx.

## 7) Qué falta para multi-tenant SaaS real

Actualmente hay base funcional, pero para SaaS multi-tenant productivo faltaría:

- Persistencia real (PostgreSQL) con aislamiento por tenant.
- Migraciones (Alembic) y modelo de datos formal (tenant, users, roles, memberships, billing).
- Autenticación/autorización robusta (JWT/OAuth2, RBAC por tenant, auditoría).
- Gestión de secretos por tenant (UISP/OpenAI/n8n/Google) con cifrado en reposo.
- Worker asíncrono/colas (Celery/RQ/Arq) para automatizaciones y webhooks.
- Idempotencia, retries, dead-letter queues para integraciones externas.
- Observabilidad (logs estructurados, métricas, tracing, alertas).
- Hardening de seguridad (rate limit, CORS estricto, CSP, rotación de keys).
- CI/CD y entornos (dev/stage/prod) con pruebas e2e.
- Billing/subscription para sub-arriendo multi-compañía.

## 8) Propuesta de plan en 10 commits pequeños (solo títulos)

1. `chore(db): add PostgreSQL config and SQLAlchemy base models`
2. `feat(tenancy): introduce Tenant, Membership and scoped repositories`
3. `feat(auth): add JWT login and tenant-aware RBAC middleware`
4. `feat(migrations): add Alembic baseline and initial schema`
5. `feat(secrets): encrypt tenant integration credentials at rest`
6. `feat(queue): add background job worker for automations and webhooks`
7. `feat(integrations): implement UISP and n8n clients with retries/idempotency`
8. `feat(frontend): add auth flow and tenant switcher in React app`
9. `chore(observability): structured logging, metrics and health probes`
10. `chore(ci): add pipeline for tests, lint, build and deploy artifacts`
