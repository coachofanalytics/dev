from main.models import ContractEvent


def record_event(contract_package, event_type, actor, payload):
	return ContractEvent.objects.create(
		contract_package=contract_package,
		event_type=event_type,
		actor=actor,
		payload=payload,
	)
