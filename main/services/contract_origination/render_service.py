from jinja2 import BaseLoader, Environment, StrictUndefined

from .exceptions import RenderError


def render_html(template_body, context):
	try:
		environment = Environment(
			loader=BaseLoader(),
			autoescape=True,
			undefined=StrictUndefined,
		)
		template = environment.from_string(template_body)
		return template.render(context)
	except Exception as exc:
		raise RenderError("Failed to render template.") from exc
