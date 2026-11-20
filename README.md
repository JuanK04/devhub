# DevHub

Aplicación web dinámica (Flask + SQLAlchemy) con catálogo de videos de YouTube sobre
programación, ciberseguridad e IA con agentes. Interfaz responsiva, base de datos
PostgreSQL en Render (SQLite en local) y panel de administración para agregar más recursos.

## Probar en local
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ADMIN_PASSWORD=miclave python app.py                # Windows: set ADMIN_PASSWORD=miclave
Abre http://127.0.0.1:5000 — el panel está en /login.

## Desplegar en Render
1. Sube esta carpeta a un repositorio de GitHub.
2. En Render: New + > Blueprint, selecciona el repositorio (usa `render.yaml`).
3. Cuando lo pida, define `ADMIN_PASSWORD` (contraseña del panel /admin).
4. Render crea la base de datos y el servicio; las tablas y los 16 videos iniciales se cargan solos.

## Agregar recursos en el futuro
Entra a `/login` > Administrar. Puedes agregar videos de YouTube (máximo 30, configurable con
`MAX_VIDEOS`) o enlaces a otras plataformas (sin límite), y eliminar los existentes.

## Notas
- Verifica en Render las condiciones vigentes del plan gratuito de PostgreSQL (puede tener caducidad).
- Cambia `SECRET_KEY` y usa una `ADMIN_PASSWORD` robusta en producción.
