# API Contract

## Base URL

- `http://localhost:8000/api`

## Endpoints iniciales

- `POST /auth/login`
- `POST /auth/register`
- `GET /dashboard`
- `GET /appointments`
- `GET /users/me`
- `PUT /users/me`

## Reglas

- JWT en `Authorization: Bearer <token>`
- Manejar 401 como sesión expirada
- Manejar 403 como acceso por rol
- Manejar 422 como validación de formulario
