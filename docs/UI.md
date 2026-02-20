# UI (Frontend Vite/React)

Se mejoró la UI de `web/` con estilo tipo consola NOC/UISP:

- Layout principal con **sidebar + topbar + content**.
- **Rutas protegidas simuladas** con mock session (`/login` y navegación interna).
- Páginas:
  - Dashboard
  - Empresas
  - Clientes
  - Integraciones
  - Monitoreo
  - Comunicaciones
  - Configuración
- Componentes UI:
  - Cards de KPIs
  - Badges de estado
  - Tabla con búsqueda + filtro
- Mantiene variables existentes:
  - `VITE_API_BASE_URL`
  - `VITE_API_KEY`

## Ejecutar frontend

```bash
cd web
npm install
npm run dev
```

## Build

```bash
cd web
npm run build
```
