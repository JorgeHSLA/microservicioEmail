# Mail Microservice

Microservicio de envío de correos electrónicos para la plataforma de turismo. Recibe solicitudes HTTP y envía correos vía Gmail SMTP con templates HTML profesionales.

## Arquitectura en capas

```
Controller (api/routers) → Service (services) → Infrastructure (smtp + templates)
```

- **Controller**: HTTP, validación Pydantic, traduce excepciones a HTTP status
- **Service**: orquesta renderer + SMTP client
- **Infrastructure**: encapsula smtplib y Jinja2
- **Schemas**: DTOs Pydantic (EmailRequest, EmailResponse)
- **Core**: configuración y excepciones de dominio

## Requisitos

- Python 3.11+
- Cuenta Gmail con [App Password](https://support.google.com/accounts/answer/185833)

## Instalación local

```bash
cd mail-service
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales Gmail
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t mail-service .
docker run --env-file .env -p 8000:8000 mail-service
```

## Endpoints

### POST /api/v1/emails

Envía un correo electrónico.

```bash
curl -X POST "http://localhost:8000/api/v1/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "to_emails": ["destino@example.com"],
    "subject": "Confirmación de reserva",
    "body": "Tu paquete turístico ha sido confirmado exitosamente."
  }'
```

**Response 200:**
```json
{"status": "sent", "recipients": ["destino@example.com"]}
```

**Errores:** 422 (validación), 502 (fallo SMTP)

### GET /health

```bash
curl http://localhost:8000/health
```

**Response:** `{"status": "ok"}`

## Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `GMAIL_USER` | Correo Gmail | (requerido) |
| `GMAIL_PASSWORD` | App Password de Gmail | (requerido) |
| `GMAIL_HOST` | Host SMTP | smtp.gmail.com |
| `GMAIL_PORT` | Puerto SMTP | 587 |
| `FROM_NAME` | Nombre del remitente | Turismo Platform |
| `TEMPLATES_DIR` | Directorio de templates | app/templates |

## Tests

```bash
pytest -v
```

## Extensibilidad

Para agregar nuevos templates de correo:
1. Crear un nuevo archivo HTML en `app/templates/` que extienda `base.html`
2. Agregar un nuevo método en `EmailService` que renderice el nuevo template
3. Crear un nuevo endpoint o parámetro en el existente
