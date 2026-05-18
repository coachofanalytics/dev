from main.models import PackageDefinition

from .exceptions import PackageDefinitionNotFoundError


PLACEMENT_PACKAGE_SLUG = "placement_standard_v1"


def get_package_definition_by_slug(slug):
	try:
		return PackageDefinition.objects.get(slug=slug)
	except PackageDefinition.DoesNotExist as exc:
		raise PackageDefinitionNotFoundError(
			f"PackageDefinition not found for slug: {slug}"
		) from exc


def get_package_definition_for_placement():
	return get_package_definition_by_slug(PLACEMENT_PACKAGE_SLUG)
