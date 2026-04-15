from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from app.core.exceptions import EmailSendError


class EmailTemplateRenderer:
    def __init__(self, templates_dir: str) -> None:
        self._env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True,
        )

    def render(self, template_name: str, context: dict) -> str:
        try:
            template = self._env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound as exc:
            raise EmailSendError(
                message=f"Template not found: {template_name}",
                original_error=exc,
            ) from exc
