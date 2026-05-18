from .exceptions import MergeValidationError


def build_merge_context(placement):
	return {
		"candidate_name": placement.candidate,
		"company_name": placement.employer,
		"salary": placement.salary,
		"placement_fee": placement.placement_fee,
		"start_date": placement.start_date.isoformat(),
	}


def validate_merge_context(merge_schema, context):
	if not isinstance(merge_schema, dict):
		raise MergeValidationError("required_fields")

	required_fields = merge_schema.get("required_fields")
	if not isinstance(required_fields, list):
		raise MergeValidationError("required_fields")

	for field in required_fields:
		if field not in context:
			raise MergeValidationError(field)


def build_and_validate_context(placement, merge_schema):
	context = build_merge_context(placement)
	validate_merge_context(merge_schema, context)
	return context
