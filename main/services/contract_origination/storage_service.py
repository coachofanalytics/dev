import os

from django.conf import settings

from .exceptions import StorageError


def _signature_relative_path(package_id, document_id):
	return os.path.join(
		"contracts",
		"signatures",
		str(package_id),
		f"{document_id}.txt",
	)


def store_signature_artifact(package_id, document_id, content):
	relative_path = _signature_relative_path(package_id, document_id)
	absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
	directory = os.path.dirname(absolute_path)

	try:
		os.makedirs(directory, exist_ok=True)
		with open(absolute_path, "w", encoding="utf-8") as handle:
			handle.write(content)
	except OSError as exc:
		raise StorageError("Failed to store signature artifact.") from exc

	return relative_path
