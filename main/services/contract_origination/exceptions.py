class ContractOriginationError(Exception):
	"""Base error for COP service layer."""


class PackageDefinitionNotFoundError(ContractOriginationError):
	"""Raised when a required package definition cannot be resolved."""


class TemplateVersionNotFoundError(ContractOriginationError):
	"""Raised when no published template version exists for a template."""


class TemplateVersionConflictError(ContractOriginationError):
	"""Raised when multiple published template versions exist."""


class MergeValidationError(ContractOriginationError):
	"""Raised when merge context does not satisfy required fields."""

	def __init__(self, missing_field):
		message = f"Missing required merge field: {missing_field}"
		super().__init__(message)
		self.missing_field = missing_field


class RenderError(ContractOriginationError):
	"""Raised when template rendering fails."""


class InvalidTransitionError(ContractOriginationError):
	"""Raised when an invalid lifecycle transition is requested."""


class TokenVerificationError(ContractOriginationError):
	"""Raised when a signing token cannot be verified."""


class SignatureVerificationError(ContractOriginationError):
	"""Raised when signature validation fails."""


class StorageError(ContractOriginationError):
	"""Raised when artifact storage fails."""
