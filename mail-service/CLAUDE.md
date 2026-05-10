# mail-service

## 1. Propósito

Microservicio FastAPI responsable del envío de **correos transaccionales** de la plataforma TuViaje.com (confirmaciones de reserva, comprobantes de pago, notificaciones genéricas). Recibe un payload simple (`to_emails`, `subject`, `body`) y lo envía vía **Gmail SMTP** usando una `App Password`. Las plantillas HTML se renderizan con **Jinja2** desde un directorio configurable.

El servicio es stateless: no persiste correos enviados, no encola, no hace retry. Si Gmail falla, devuelve 502 y el cliente decide si reintenta.

## 2. Estructura de carpetas

```
mail-service/
├── Dockerfile
├── requirements.txt
├── .env / .env.example
├── README.md
├── tests/
└── app/
    ├── main.py                       # create_app(): registra health_router + email_router
    ├── api/
    │   ├── dependencies.py           # get_email_service() → DI de EmailService
    │   └── routers/
    │       ├── health_router.py      # GET /api/v1/health → {"status":"ok","service":"mail-service"}
    │       └── email_router.py       # POST /api/v1/emails
    ├── services/
    │   └── email_service.py          # Lógica de envío (orquesta renderer + smtp client)
    ├── infrastructure/
    │   ├── smtp/
    │   │   └── gmail_smtp_client.py  # Cliente SMTP (smtplib + STARTTLS)
    │   └── templates/
    │       └── template_renderer.py  # Jinja2 Environment + FileSystemLoader
    ├── schemas/
    │   └── email_schemas.py          # EmailRequest / EmailResponse
    ├── core/
    │   ├── config.py                 # Settings (lee .env)
    │   └── exceptions.py             # EmailSendError
    └── templates/
        ├── base.html                 # Layout base
        └── generic_message.html      # Plantilla de mensaje genérico
```

| Subdir | Responsabilidad |
|--------|-----------------|
| `api/routers` | Capa HTTP. Convierte `EmailSendError` en `HTTPException(502)`. |
| `api/dependencies` | Wiring por `Depends`: construye `EmailService` con sus colaboradores. |
| `services` | Orquesta renderer + SMTP client. |
| `infrastructure/smtp` | Único módulo que habla con Gmail SMTP. |
| `infrastructure/templates` | Único módulo que renderiza Jinja2. |
| `schemas` | DTOs Pydantic con `EmailStr` (valida el formato de email). |
| `core` | Configuración (`Settings`) y excepciones de dominio. |
| `templates` | HTML estáticos (Jinja2). `TEMPLATES_DIR=app/templates` por default. |

## 3. Endpoints

| Método | Path | Descripción | Status OK | Errores posibles |
|--------|------|-------------|-----------|------------------|
| POST | `/api/v1/emails` | Envía un correo a uno o varios destinatarios usando Gmail SMTP. | `200 EmailResponse` | `400` validación, `502` SMTP falló |
| GET | `/api/v1/health` | Liveness probe — `{"status":"ok","service":"mail-service"}`. | `200` | — |

## 4. Esquemas JSON (wire format)

### Request — `POST /api/v1/emails`
```json
{
  "toEmails": ["jorgesierralaiton@gmail.com", "otro@example.com"],
  "subject": "Confirmación de reserva TuViaje.com",
  "body": "Tu reserva BOG-MDE ha sido confirmada. Código: ABC123."
}
```

Reglas de validación (Pydantic):
- `toEmails` (alias de `to_emails`): lista no vacía de `EmailStr` (formato RFC válido).
- `subject`: 1–255 caracteres.
- `body`: mínimo 1 caracter.

> Nota: el wire JSON acepta tanto `toEmails` (camelCase, **forma canónica**, alineada con `banco-service`) como `to_emails` (snake_case, **legacy**, se mantiene por compatibilidad con clientes Spring existentes). Esto es posible gracias a `alias="toEmails"` + `populate_by_name=True` en `EmailRequest`. La salida por defecto del schema utiliza el nombre Python (`to_emails`) salvo que el cliente serialice por alias.

### Response 200 — `EmailResponse`
```json
{
  "status": "sent",
  "recipients": ["jorgesierralaiton@gmail.com", "otro@example.com"]
}
```

### Response 200 — `GET /api/v1/health`
```json
{ "status": "ok", "service": "mail-service" }
```

## 5. Manejo de errores

A diferencia del banco-service, este servicio usa **el formato por defecto de FastAPI** (`{"detail": ...}`).

### 400 — Validation error
Devuelto automáticamente por FastAPI/Pydantic cuando `toEmails` (o `to_emails`) está vacío, hay un email malformado, `subject` excede 255 chars, etc.
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "toEmails", 0],
      "msg": "value is not a valid email address: ...",
      "input": "no-es-un-email"
    }
  ]
}
```

### 502 — SMTP send failure
`EmailSendError` se levanta desde `gmail_smtp_client.py` (auth error, Gmail caído, timeout) o desde `template_renderer.py` (template no encontrado). El router lo captura y retorna:
```json
{ "detail": "SMTP authentication failed: Username and Password not accepted" }
```

| HTTP | `detail` (string) | Cuándo |
|------|-------------------|--------|
| 400 | array Pydantic | Body inválido. |
| 502 | string descriptivo | SMTP auth error, Gmail timeout, host inalcanzable, plantilla no encontrada. |

## 6. Variables de entorno

| Variable | Default | Uso |
|----------|---------|-----|
| `GMAIL_USER` | — (requerido) | Cuenta Gmail emisora (ej. `tu@gmail.com`). |
| `GMAIL_PASSWORD` | — (requerido) | **Gmail App Password** (16 caracteres). NO la contraseña normal. |
| `GMAIL_HOST` | `smtp.gmail.com` | Host SMTP. |
| `GMAIL_PORT` | `587` | Puerto SMTP (STARTTLS). |
| `FROM_NAME` | `Turismo Platform` | Display name del remitente. |
| `TEMPLATES_DIR` | `app/templates` | Directorio para Jinja2 `FileSystemLoader`. |

## 7. Cómo correr

### Local (uvicorn)
```bash
cd microservicioEmail/mail-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# editar .env con GMAIL_USER + GMAIL_PASSWORD (App Password)
uvicorn app.main:app --reload --port 8000
```

### Docker / docker compose
```bash
docker build -t mail-service .
docker run --env-file .env -p 8000:8000 mail-service
# o:
docker compose up email
```

### Tests
```bash
pytest tests/
```

OpenAPI interactivo: `http://localhost:8000/docs`.

## 8. Cómo lo consume el backend Spring

Spring lo invoca al final del checkout (después de un pago aprobado por `banco-service`) y al confirmar/cancelar reservas.

### curl de ejemplo
```bash
curl -X POST http://localhost:8000/api/v1/emails \
  -H "Content-Type: application/json" \
  -d '{
        "toEmails": ["jorgesierralaiton@gmail.com"],
        "subject": "Confirmación de reserva TuViaje.com",
        "body": "Tu reserva BOG-MDE ha sido confirmada."
      }'
```

### Cliente Java (`MailClient`)
Ubicado en `tuViajeBackend/src/main/java/.../client/MailClient.java`:

```java
@Component
public class MailClient {

    private final RestClient restClient;

    public MailClient(@Value("${mail.base-url}") String baseUrl) {
        this.restClient = RestClient.builder()
            .baseUrl(baseUrl)              // http://mail-service:8000
            .defaultHeader("Content-Type", "application/json")
            .build();
    }

    public EmailResponse send(EmailRequest req) {
        return restClient.post()
            .uri("/api/v1/emails")
            .body(req)
            .retrieve()
            .onStatus(HttpStatusCode::isError, (request, response) -> {
                throw new MailIntegrationException(response.getStatusCode(),
                    new String(response.getBody().readAllBytes()));
            })
            .body(EmailResponse.class);
    }
}
```

Los DTO Java pueden serializar directamente con Jackson en camelCase (`toEmails`) — esa es la forma canónica del contrato. Como el servicio acepta también `to_emails` por compatibilidad, los clientes Java existentes con `@JsonProperty("to_emails")` o `PropertyNamingStrategy.SNAKE_CASE` siguen funcionando sin cambios.

## 9. Notas para sesiones futuras de Claude

- **Gmail App Password obligatorio**: con la contraseña normal Gmail rechaza el login (devuelve `534-5.7.9`). Generar en `https://myaccount.google.com/apppasswords` con 2FA activo.
- **Puerto 587 + STARTTLS**, no 465. El cliente en `gmail_smtp_client.py` hace `smtplib.SMTP(host, 587)` + `starttls()`.
- **`/api/v1/health`**: el health-check está bajo el mismo prefix `/api/v1` que el resto de la API. Si se agrega un gateway, mantener el prefix.
- **camelCase + snake_case en el wire**: la forma canónica es `toEmails` (camelCase, alineada con `banco-service`). El servicio también acepta `to_emails` (snake_case) como legacy gracias a `alias="toEmails"` + `populate_by_name=True` en `EmailRequest`. Nuevos clientes deben usar `toEmails`.
- **Jinja2 autoescape activo**: los valores que entren a una plantilla se escapan como HTML. Si se necesita inyectar HTML literal, marcarlo con `{{ value | safe }}` deliberadamente.
- **`base.html` + `generic_message.html`**: las plantillas existen pero el endpoint actual envía el `body` como texto plano sin pasar por el renderer. Si se quiere usar plantillas, modificar `EmailService.send_email` para invocar `EmailTemplateRenderer.render(...)` antes del envío SMTP.
- **Sin retry, sin cola**: si Gmail falla, el cliente recibe 502 y debe reintentar él mismo. Para producción agregar Celery/RQ + Redis.
- **Logging**: usar `logging` (no `print`). Filtrar `GMAIL_PASSWORD` de cualquier log.
- **Tests**: `tests/` existe pero no validar contra Gmail real — mockear `smtplib.SMTP` con `unittest.mock.patch`.
