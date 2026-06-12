import os
import tempfile
from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from main.models import (
    CandidatePlacement,
    ContractDocument,
    ContractEvent,
    ContractPackage,
    ContractSignature,
    ContractTemplate,
    ContractTemplateVersion,
    PackageDefinition,
    PackageDefinitionDocument,
)
from main.services.contract_origination import audit_service
from main.services.contract_origination import merge_service
from main.services.contract_origination import origination
from main.services.contract_origination import pdf_service
from main.services.contract_origination import registry
from main.services.contract_origination import render_service
from main.services.contract_origination import signature_service
from main.services.contract_origination import storage_service
from main.services.contract_origination import template_service
from main.services.contract_origination.exceptions import (
    InvalidTransitionError,
    MergeValidationError,
    PackageDefinitionNotFoundError,
    RenderError,
    SignatureVerificationError,
    TemplateVersionConflictError,
    TemplateVersionNotFoundError,
    TokenVerificationError,
)


class RegistryServiceTests(TestCase):
    def test_get_package_definition_for_placement(self):
        package_definition = PackageDefinition.objects.create(
            name="Placement Standard v1",
            slug="placement_standard_v1",
            merge_schema={"required_fields": []},
        )

        resolved = registry.get_package_definition_for_placement()

        self.assertEqual(resolved, package_definition)

    def test_get_package_definition_by_slug_missing(self):
        with self.assertRaises(PackageDefinitionNotFoundError):
            registry.get_package_definition_by_slug("missing")


class TemplateServiceTests(TestCase):
    def test_get_published_template_version_missing(self):
        template = ContractTemplate.objects.create(
            name="Placement Agreement",
            slug="placement_agreement",
        )

        with self.assertRaises(TemplateVersionNotFoundError):
            template_service.get_published_template_version(template)

    def test_get_published_template_version_conflict(self):
        template = ContractTemplate.objects.create(
            name="Placement Agreement",
            slug="placement_agreement",
        )
        ContractTemplateVersion.objects.create(
            contract_template=template,
            version=1,
            template_body="A",
            is_published=True,
        )
        ContractTemplateVersion.objects.create(
            contract_template=template,
            version=2,
            template_body="B",
            is_published=True,
        )

        with self.assertRaises(TemplateVersionConflictError):
            template_service.get_published_template_version(template)

    def test_get_published_template_version_success(self):
        template = ContractTemplate.objects.create(
            name="Placement Agreement",
            slug="placement_agreement",
        )
        version = ContractTemplateVersion.objects.create(
            contract_template=template,
            version=1,
            template_body="A",
            is_published=True,
        )

        resolved = template_service.get_published_template_version(template)

        self.assertEqual(resolved, version)


class MergeServiceTests(TestCase):
    def test_build_merge_context(self):
        package_definition = PackageDefinition.objects.create(
            name="Placement Standard v1",
            slug="placement_standard_v1",
            merge_schema={"required_fields": []},
        )
        contract_package = ContractPackage.objects.create(
            package_definition=package_definition,
            state=ContractPackage.State.DRAFT,
            origination_key="orig-1",
        )
        placement = CandidatePlacement.objects.create(
            candidate="Alice",
            candidate_email="alice@example.com",
            employer="Acme",
            salary=Decimal("4000.00"),
            placement_fee=Decimal("2000.00"),
            start_date=date(2026, 6, 1),
            contract_package=contract_package,
        )

        context = merge_service.build_merge_context(placement)

        self.assertEqual(context["candidate_name"], "Alice")
        self.assertEqual(context["company_name"], "Acme")
        self.assertEqual(context["salary"], Decimal("4000.00"))
        self.assertEqual(context["placement_fee"], Decimal("2000.00"))
        self.assertEqual(context["start_date"], "2026-06-01")

    def test_validate_merge_context_missing_field(self):
        merge_schema = {"required_fields": ["candidate_name", "salary"]}
        context = {"candidate_name": "Alice"}

        with self.assertRaises(MergeValidationError) as context_manager:
            merge_service.validate_merge_context(merge_schema, context)

        self.assertEqual(context_manager.exception.missing_field, "salary")

    def test_validate_merge_context_invalid_schema(self):
        with self.assertRaises(MergeValidationError):
            merge_service.validate_merge_context(None, {})


class RenderServiceTests(TestCase):
    def test_render_html_success(self):
        html = render_service.render_html(
            "Hello {{ candidate_name }}",
            {"candidate_name": "Alice"},
        )

        self.assertEqual(html, "Hello Alice")

    def test_render_html_missing_variable(self):
        with self.assertRaises(RenderError):
            render_service.render_html("Hello {{ missing }}", {})


class StorageServiceTests(TestCase):
    def test_store_signature_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=temp_dir):
                relative_path = storage_service.store_signature_artifact(
                    package_id=1001,
                    document_id=2001,
                    content="signed",
                )
                absolute_path = os.path.join(temp_dir, relative_path)

                self.assertTrue(os.path.exists(absolute_path))
                with open(absolute_path, "r", encoding="utf-8") as handle:
                    self.assertEqual(handle.read(), "signed")


class AuditServiceTests(TestCase):
    def test_record_event(self):
        package_definition = PackageDefinition.objects.create(
            name="Placement Standard v1",
            slug="placement_standard_v1",
            merge_schema={"required_fields": []},
        )
        contract_package = ContractPackage.objects.create(
            package_definition=package_definition,
            state=ContractPackage.State.DRAFT,
            origination_key="orig-2",
        )

        event = audit_service.record_event(
            contract_package=contract_package,
            event_type="GENERATED",
            actor="system",
            payload={"state": "GENERATED"},
        )

        self.assertEqual(ContractEvent.objects.count(), 1)
        self.assertEqual(event.contract_package, contract_package)
        self.assertEqual(event.event_type, "GENERATED")


class SignatureServiceTests(TestCase):
    def _create_package_with_document(self):
        package_definition = PackageDefinition.objects.create(
            name="Placement Standard v1",
            slug="placement_standard_v1",
        )
        contract_package = ContractPackage.objects.create(
            package_definition=package_definition,
            state=ContractPackage.State.GENERATED,
            origination_key="orig-3",
        )
        CandidatePlacement.objects.create(
            candidate="Alice",
            candidate_email="alice@example.com",
            employer="Acme",
            salary=Decimal("4000.00"),
            placement_fee=Decimal("2000.00"),
            start_date=date(2026, 6, 1),
            contract_package=contract_package,
        )
        template = ContractTemplate.objects.create(
            name="Placement Agreement",
            slug="placement_agreement",
        )
        version = ContractTemplateVersion.objects.create(
            contract_template=template,
            version=1,
            template_body="Hello",
            is_published=True,
        )
        document = ContractDocument.objects.create(
            contract_package=contract_package,
            contract_template_version=version,
            html_snapshot="<html>Snapshot</html>",
        )
        return contract_package, document

    def test_generate_and_verify_token(self):
        contract_package, document = self._create_package_with_document()
        token = signature_service.generate_signing_token(document)

        resolved = signature_service.verify_signing_token(token)

        self.assertEqual(resolved, document)
        self.assertEqual(resolved.contract_package, contract_package)

    def test_verify_signing_token_invalid(self):
        with self.assertRaises(TokenVerificationError):
            signature_service.verify_signing_token("invalid")

    def test_sign_document_success(self):
        contract_package, document = self._create_package_with_document()
        signature_service.mark_package_sent(contract_package)
        token = signature_service.generate_signing_token(document)

        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=temp_dir):
                signature = signature_service.sign_document(
                    token=token,
                    signer_name="Alice",
                    ip_address="203.0.113.10",
                    method="ESIGN",
                )

        contract_package.refresh_from_db()

        self.assertEqual(signature.contract_document, document)
        self.assertEqual(contract_package.state, ContractPackage.State.EXECUTED)
        self.assertEqual(ContractSignature.objects.count(), 1)

    def test_sign_document_rejects_name_mismatch(self):
        contract_package, document = self._create_package_with_document()
        signature_service.mark_package_sent(contract_package)
        token = signature_service.generate_signing_token(document)

        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=temp_dir):
                with self.assertRaises(SignatureVerificationError):
                    signature_service.sign_document(
                        token=token,
                        signer_name="Bob",
                        ip_address="203.0.113.10",
                        method="ESIGN",
                    )

        self.assertEqual(ContractSignature.objects.count(), 0)

    def test_mark_package_sent_invalid_state(self):
        package_definition = PackageDefinition.objects.create(
            name="Placement Standard v1",
            slug="placement_standard_v1",
            merge_schema={"required_fields": []},
        )
        contract_package = ContractPackage.objects.create(
            package_definition=package_definition,
            state=ContractPackage.State.DRAFT,
            origination_key="orig-4",
        )

        with self.assertRaises(InvalidTransitionError):
            signature_service.mark_package_sent(contract_package)


class OriginationServiceTests(TestCase):
    def _setup_package_definition(self):
        package_definition = PackageDefinition.objects.create(
            name="Placement Standard v1",
            slug="placement_standard_v1",
            merge_schema={
                "required_fields": [
                    "candidate_name",
                    "company_name",
                    "salary",
                    "placement_fee",
                    "start_date",
                ]
            },
        )
        template = ContractTemplate.objects.create(
            name="Placement Agreement",
            slug="placement_agreement",
        )
        ContractTemplateVersion.objects.create(
            contract_template=template,
            version=1,
            template_body="Hello {{ candidate_name }}",
            is_published=True,
        )
        template_version = ContractTemplateVersion.objects.first()
        PackageDefinitionDocument.objects.create(
            package_definition=package_definition,
            contract_template_version=template_version,
            order=1,
        )
        return package_definition

    def test_originate_contract_package(self):
        self._setup_package_definition()
        placement = CandidatePlacement.objects.create(
            candidate="Alice",
            candidate_email="alice@example.com",
            employer="Acme",
            salary=Decimal("4000.00"),
            placement_fee=Decimal("2000.00"),
            start_date=date(2026, 6, 1),
            contract_package=None,
        )

        contract_package = origination.originate_contract_package(placement.id)

        placement.refresh_from_db()
        contract_package.refresh_from_db()

        self.assertEqual(placement.contract_package, contract_package)
        self.assertEqual(contract_package.state, ContractPackage.State.GENERATED)
        self.assertEqual(contract_package.documents.count(), 1)
        self.assertIn("Alice", contract_package.documents.first().html_snapshot)
        self.assertEqual(ContractEvent.objects.count(), 1)

    def test_originate_contract_package_idempotent(self):
        package_definition = self._setup_package_definition()
        placement = CandidatePlacement.objects.create(
            candidate="Alice",
            candidate_email="alice@example.com",
            employer="Acme",
            salary=Decimal("4000.00"),
            placement_fee=Decimal("2000.00"),
            start_date=date(2026, 6, 1),
            contract_package=None,
        )
        existing = ContractPackage.objects.create(
            package_definition=package_definition,
            state=ContractPackage.State.DRAFT,
            origination_key=f"candidate_placement:{placement.id}",
        )

        resolved = origination.originate_contract_package(placement.id)

        placement.refresh_from_db()
        self.assertEqual(resolved, existing)
        self.assertEqual(placement.contract_package, existing)


class PdfServiceTests(TestCase):
    def test_pdf_service_stub(self):
        with self.assertRaises(NotImplementedError):
            pdf_service.render_pdf_from_html_snapshot("<html></html>")
