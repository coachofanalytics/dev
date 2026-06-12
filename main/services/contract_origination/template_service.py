from main.models import ContractTemplateVersion

from .exceptions import TemplateVersionConflictError, TemplateVersionNotFoundError


def get_published_template_version(contract_template):
	versions = ContractTemplateVersion.objects.filter(
		contract_template=contract_template,
		is_published=True,
	)

	count = versions.count()
	if count == 0:
		raise TemplateVersionNotFoundError(
			"No published template version found for template."
		)
	if count > 1:
		raise TemplateVersionConflictError(
			"Multiple published template versions found for template."
		)

	return versions.first()
