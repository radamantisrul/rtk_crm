# RTK CRM Monorepo (API + Frontend)

Este repo ahora tiene:

- `app/`: API FastAPI (multi-compañía, customers, automatizaciones, dashboard)
- `web/`: Frontend React + Vite que consume la API
- `nginx/`: ejemplos de configuración para VPS
- `docker-compose.yml`: opción para levantar API + frontend juntos en local

## Estructura

```text
/app
/web
/nginx
/docker-compose.yml
```

## 1) Correr API (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

API en `http://localhost:8000`.

### API Key (opcional)

Si defines `RTK_API_KEY`, la API exige header `x-api-key` en endpoints de negocio (`/companies`, `/customers`, etc.).
`/health` queda público.

```bash
export RTK_API_KEY="mi-clave-segura"
```

## 2) Correr Frontend (React + Vite)

```bash
cd web
cp .env.example .env
npm install
npm run dev
```

Frontend en `http://localhost:5173`.

Variables de entorno frontend:

- `VITE_API_BASE_URL` (ej: `http://localhost:8000` o `/api` detrás de Nginx)
- `VITE_API_KEY` (opcional, si habilitas `RTK_API_KEY` en la API)

## 3) Pantallas implementadas

- Home / Dashboard: muestra estado API con `GET /health`
- Companies: listar (`GET /companies`) y crear (`POST /companies`)
- Customers: crear (`POST /companies/{company_id}/customers`)

Incluye estados de loading y manejo de errores en UI.

## 4) Deploy en VPS detrás de Nginx

### Build frontend

```bash
cd web
npm install
VITE_API_BASE_URL=/api npm run build
```

Publica `web/dist` en `/var/www/rtk-crm-web`.

### Ejecutar API en VPS

Ejemplo con uvicorn:

```bash
cd /ruta/del/repo
python -m venv .venv
source .venv/bin/activate
pip install -e .
export RTK_API_KEY="mi-clave-segura"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Config Nginx

Usa como base `nginx/vps.conf` (ajusta `server_name`).

- `/api/` proxya a FastAPI (`127.0.0.1:8000`)
- `/` sirve SPA React desde `/var/www/rtk-crm-web`

## 5) Opción docker-compose (local)

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

> No rompe el deploy actual: es una opción adicional de desarrollo local.

## Testing

```bash
pytest -q
```
