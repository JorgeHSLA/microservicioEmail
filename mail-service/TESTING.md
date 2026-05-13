# mail-service — Guía de pruebas

Microservicio FastAPI que envía correos vía Gmail SMTP usando plantillas Jinja2.

## 1. Levantar el servicio

### Con Docker

```bash
cp .env.example .env
# Edita .env con credenciales reales de Gmail (GMAIL_USER, GMAIL_PASSWORD = app password)
docker build -t mail-service .
docker run --rm --env-file .env -p 8000:8000 mail-service
```

### Con Python local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Swagger UI: <http://localhost:8000/docs>

## 2. Variables de entorno

| Variable | Para qué |
|---|---|
| `GMAIL_USER` | Cuenta Gmail desde la que se envía. |
| `GMAIL_PASSWORD` | App password de Gmail (NO la contraseña normal). |
| `GMAIL_HOST` | `smtp.gmail.com` |
| `GMAIL_PORT` | `587` |
| `FROM_NAME` | Nombre amigable del remitente (`TuViaje.com`). |
| `TEMPLATES_DIR` | `app/templates` |

> Obtener app password en <https://myaccount.google.com/apppasswords> (requiere 2FA activado).

## 3. Endpoints

| Método | Path | Notas |
|---|---|---|
| GET  | `/health` | Liveness. |
| POST | `/api/v1/emails` | Envía un email a una lista de destinatarios. |

## 4. Smoke tests

### A) Health

```bash
curl -s http://localhost:8000/health
# {"status":"ok"}
```

### B) Enviar email

```bash
curl -s -X POST http://localhost:8000/api/v1/emails \
  -H 'Content-Type: application/json' \
  -d '{
    "to_emails": ["destinatario@gmail.com"],
    "subject": "Confirmación de reserva TuViaje",
    "body": "Tu reserva ha sido confirmada con éxito."
  }' | python3 -m json.tool
# {"status":"sent","recipients":["destinatario@gmail.com"]}
```

### C) Validación

```bash
# to_emails vacío
curl -s -X POST http://localhost:8000/api/v1/emails \
  -H 'Content-Type: application/json' \
  -d '{"to_emails":[],"subject":"x","body":"y"}'
# 422

# Email mal formado
curl -s -X POST http://localhost:8000/api/v1/emails \
  -H 'Content-Type: application/json' \
  -d '{"to_emails":["no-es-email"],"subject":"x","body":"y"}'
# 422
```

### D) Tests automatizados

El repo trae carpeta `tests/`:

```bash
pytest tests/ -v
```

## 5. Conocido

- Sin credenciales válidas el servicio arranca pero los POST a `/emails` fallan en SMTP (500). Configura `GMAIL_USER` + app password antes de probar envío real.
- Gmail rate-limita ~500 envíos/día por cuenta gratis.
