from django.db import transaction

from main.models import CandidatePlacement, ContractPackage, ContractDocument

from .audit_service import record_event
from .exceptions import ContractOriginationError, InvalidTransitionError
from .merge_service import build_and_validate_context
from .registry import get_package_definition_for_placement
from .render_service import render_html


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


def originate_contract_package(placement_id, actor="system", origination_key=None):
	placement = CandidatePlacement.objects.select_related(
		"contract_package",
		"package_definition",
	).get(id=placement_id)

	if placement.contract_package:
		return placement.contract_package

	package_definition = placement.package_definition
	if not package_definition:
		package_definition = get_package_definition_for_placement()
	if not origination_key:
		origination_key = f"candidate_placement:{placement.id}"

	existing = ContractPackage.objects.filter(
		origination_key=origination_key
	).first()
	if existing:
		placement.contract_package = existing
		placement.save(update_fields=["contract_package", "updated_at"])
		return existing

	documents = package_definition.documents.order_by("order", "id")
	if not documents.exists():
		raise ContractOriginationError(
			"PackageDefinition has no documents configured."
		)

	with transaction.atomic():
		contract_package = ContractPackage.objects.create(
			package_definition=package_definition,
			state=ContractPackage.State.DRAFT,
			origination_key=origination_key,
		)
		placement.contract_package = contract_package
		placement.save(update_fields=["contract_package", "updated_at"])

		for document_def in documents:
			template_version = document_def.contract_template_version
			context = build_and_validate_context(
				placement,
				package_definition.merge_schema,
			)
			html = render_html(template_version.template_body, context)
			ContractDocument.objects.create(
				contract_package=contract_package,
				contract_template_version=template_version,
				html_snapshot=html,
			)

		_transition_state(contract_package, ContractPackage.State.GENERATED)
		record_event(
			contract_package,
			event_type="GENERATED",
			actor=actor,
			payload={
				"state": ContractPackage.State.GENERATED,
				"placement_id": placement.id,
			},
		)

	return contract_package


def create_from_placement(placement_id, actor="system", origination_key=None):
	return originate_contract_package(
		placement_id,
		actor=actor,
		origination_key=origination_key,
	)
