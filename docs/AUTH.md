# AUTH mínima (admin inicial)

Se implementó autenticación básica en el backend FastAPI con un usuario admin único definido por variables de entorno.

## Variables de entorno

```bash
export RTK_ADMIN_USER="admin"
export RTK_ADMIN_PASSWORD="cambia-esta-clave"
# opcional
export RTK_AUTH_SECRET="otra-clave-larga-y-segura"
export RTK_AUTH_TTL_SECONDS="43200"
```

## Login

Endpoint:

- `POST /auth/login`

Payload:

```json
{
  "username": "admin",
  "password": "cambia-esta-clave"
}
```

Respuesta:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

## Validar sesión

Endpoint:

- `GET /auth/me`

Header requerido:

```http
Authorization: Bearer <access_token>
```

## Frontend

- El frontend usa login real en `/login`.
- Guarda `access_token` en `localStorage`.
- Revalida sesión con `/auth/me` al cargar la app.
- Protege rutas del panel y redirige a `/login` si no hay token válido.
