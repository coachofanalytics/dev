from django.core import signing
from django.utils import timezone

from main.models import CandidatePlacement, ContractPackage, ContractSignature

from .audit_service import record_event
from .exceptions import (
	InvalidTransitionError,
	SignatureVerificationError,
	TokenVerificationError,
)
from .storage_service import store_signature_artifact


SIGNING_SALT = "cop-contract-signing"
PACKAGE_SIGNING_SALT = "cop-package-signing"


def _normalize_name(value):
	return " ".join(value.strip().lower().split())


def _transition_state(contract_package, new_state):
	allowed = {
		ContractPackage.State.DRAFT: ContractPackage.State.GENERATED,
		ContractPackage.State.GENERATED: ContractPackage.State.SENT,
		ContractPackage.State.SENT: ContractPackage.State.SIGNED,
		ContractPackage.State.SIGNED: ContractPackage.State.EXECUTED,
	}

	current_state = contract_package.state
	if current_state not in allowed or allowed[current_state] != new_state:
		raise InvalidTransitionError(
			f"Invalid transition: {current_state} -> {new_state}"
		)

	contract_package.state = new_state
	contract_package.save(update_fields=["state", "updated_at"])


def generate_signing_token(contract_document):
	signer = signing.Signer(salt=SIGNING_SALT)
	value = f"{contract_document.contract_package_id}:{contract_document.id}"
	return signer.sign(value)


def generate_package_signing_token(contract_package):
	signer = signing.Signer(salt=PACKAGE_SIGNING_SALT)
	return signer.sign(str(contract_package.id))


def verify_signing_token(token):
	signer = signing.Signer(salt=SIGNING_SALT)
	try:
		value = signer.unsign(token)
	except signing.BadSignature as exc:
		raise TokenVerificationError("Invalid signing token.") from exc

	parts = value.split(":")
	if len(parts) != 2:
		raise TokenVerificationError("Invalid signing token payload.")

	package_id, document_id = parts

	try:
		document_id = int(document_id)
		package_id = int(package_id)
	except ValueError as exc:
		raise TokenVerificationError("Invalid signing token payload.") from exc

	from main.models import ContractDocument

	try:
		document = ContractDocument.objects.select_related(
			"contract_package"
		).get(id=document_id)
	except ContractDocument.DoesNotExist as exc:
		raise TokenVerificationError("Contract document not found.") from exc

	if document.contract_package_id != package_id:
		raise TokenVerificationError("Signing token does not match document.")

	return document


def verify_package_signing_token(token):
	signer = signing.Signer(salt=PACKAGE_SIGNING_SALT)
	try:
		value = signer.unsign(token)
	except signing.BadSignature as exc:
		raise TokenVerificationError("Invalid signing token.") from exc

	try:
		package_id = int(value)
	except ValueError as exc:
		raise TokenVerificationError("Invalid signing token payload.") from exc

	try:
		contract_package = ContractPackage.objects.get(id=package_id)
	except ContractPackage.DoesNotExist as exc:
		raise TokenVerificationError("Contract package not found.") from exc

	return contract_package


def _get_expected_signer_name(contract_package):
	placement = CandidatePlacement.objects.filter(
		contract_package=contract_package
	).first()
	if not placement:
		raise SignatureVerificationError(
			"CandidatePlacement not found for contract package."
		)
	return placement.candidate


def _all_documents_signed(contract_package):
	documents = contract_package.documents.all()
	if not documents.exists():
		return False

	for document in documents:
		if not ContractSignature.objects.filter(contract_document=document).exists():
			return False
	return True


def mark_package_sent(contract_package, actor="system"):
	if contract_package.state != ContractPackage.State.GENERATED:
		raise InvalidTransitionError(
			f"Invalid transition: {contract_package.state} -> SENT"
		)

	_transition_state(contract_package, ContractPackage.State.SENT)
	record_event(
		contract_package,
		event_type="SENT",
		actor=actor,
		payload={"state": ContractPackage.State.SENT},
	)


def sign_document(token, signer_name, ip_address, method):
	document = verify_signing_token(token)
	contract_package = document.contract_package

	if contract_package.state != ContractPackage.State.SENT:
		raise InvalidTransitionError(
			f"Invalid transition: {contract_package.state} -> SIGNED"
		)

	expected_name = _get_expected_signer_name(contract_package)
	if _normalize_name(signer_name) != _normalize_name(expected_name):
		raise SignatureVerificationError("Signer name does not match.")

	signed_at = timezone.now()
	artifact_content = (
		f"signer={signer_name}\n"
		f"signed_at={signed_at.isoformat()}\n"
		f"ip_address={ip_address}\n"
		f"method={method}\n"
	)
	artifact_path = store_signature_artifact(
		contract_package.id,
		document.id,
		artifact_content,
	)

	signature = ContractSignature.objects.create(
		contract_document=document,
		signer=signer_name,
		artifact=artifact_path,
		signed_at=signed_at,
		ip_address=ip_address,
		method=method,
	)

	record_event(
		contract_package,
		event_type="DOCUMENT_SIGNED",
		actor=signer_name,
		payload={"document_id": document.id},
	)

	if _all_documents_signed(contract_package):
		_transition_state(contract_package, ContractPackage.State.SIGNED)
		record_event(
			contract_package,
			event_type="SIGNED",
			actor=signer_name,
			payload={"state": ContractPackage.State.SIGNED},
		)
		_transition_state(contract_package, ContractPackage.State.EXECUTED)
		record_event(
			contract_package,
			event_type="EXECUTED",
			actor=signer_name,
			payload={"state": ContractPackage.State.EXECUTED},
		)

	return signature


def sign_package(token, signer_name, ip_address, method):
	contract_package = verify_package_signing_token(token)

	if contract_package.state != ContractPackage.State.SENT:
		raise InvalidTransitionError(
			f"Invalid transition: {contract_package.state} -> SIGNED"
		)

	expected_name = _get_expected_signer_name(contract_package)
	if _normalize_name(signer_name) != _normalize_name(expected_name):
		raise SignatureVerificationError("Signer name does not match.")

	for document in contract_package.documents.all():
		if ContractSignature.objects.filter(contract_document=document).exists():
			continue
		document_token = generate_signing_token(document)
		sign_document(
			token=document_token,
			signer_name=signer_name,
			ip_address=ip_address,
			method=method,
		)

	return contract_package
