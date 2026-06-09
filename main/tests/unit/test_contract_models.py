from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from main.models import (
    CandidatePlacement,
    ContractAttachment,
    ContractDocument,
    ContractEvent,
    ContractPackage,
    ContractSignature,
    ContractTemplate,
    ContractTemplateVersion,
    PackageDefinition,
    PackageDefinitionDocument,
)


class ContractModelTests(TestCase):
    def _create_contract_template(self):
        return ContractTemplate.objects.create(
            name="Placement Agreement",
            slug="placement_agreement",
        )

    def _create_template_version(self, contract_template=None):
        if contract_template is None:
            contract_template = self._create_contract_template()
        return ContractTemplateVersion.objects.create(
            contract_template=contract_template,
            version=1,
            template_body="<p>Template body</p>",
        )

    def _create_package_definition(self):
        return PackageDefinition.objects.create(
            name="Placement Standard v1",
            slug="placement_standard_v1",
            merge_schema={"required_fields": []},
        )

    def _create_contract_package(self, package_definition=None):
        if package_definition is None:
            package_definition = self._create_package_definition()
        return ContractPackage.objects.create(
            package_definition=package_definition,
            state=ContractPackage.State.DRAFT,
            origination_key="orig-123",
        )

    def _create_contract_document(
        self,
        contract_package=None,
        contract_template_version=None,
    ):
        if contract_package is None:
            contract_package = self._create_contract_package()
        if contract_template_version is None:
            contract_template_version = self._create_template_version()
        return ContractDocument.objects.create(
            contract_package=contract_package,
            contract_template_version=contract_template_version,
            html_snapshot="<html>Snapshot</html>",
        )

    def test_contract_template_fields_and_str(self):
        template = self._create_contract_template()

        self.assertEqual(template.name, "Placement Agreement")
        self.assertEqual(template.slug, "placement_agreement")
        self.assertIsNotNone(template.created_at)
        self.assertIsNotNone(template.updated_at)
        self.assertEqual(str(template), "Placement Agreement")

    def test_contract_template_version_defaults_and_relation(self):
        template = self._create_contract_template()
        version = self._create_template_version(contract_template=template)

        self.assertEqual(version.contract_template, template)
        self.assertEqual(version.version, 1)
        self.assertEqual(version.template_body, "<p>Template body</p>")
        self.assertFalse(version.is_published)
        self.assertIsNotNone(version.created_at)
        self.assertEqual(template.versions.count(), 1)
        self.assertEqual(template.versions.first(), version)

    def test_package_definition_fields(self):
        package_definition = self._create_package_definition()

        self.assertEqual(package_definition.name, "Placement Standard v1")
        self.assertEqual(package_definition.slug, "placement_standard_v1")
        self.assertEqual(package_definition.merge_schema, {"required_fields": []})
        self.assertIsNotNone(package_definition.created_at)
        self.assertIsNotNone(package_definition.updated_at)

    def test_package_definition_document_relation(self):
        package_definition = self._create_package_definition()
        template_version = self._create_template_version()
        document = PackageDefinitionDocument.objects.create(
            package_definition=package_definition,
            contract_template_version=template_version,
            order=1,
        )

        self.assertEqual(document.package_definition, package_definition)
        self.assertEqual(document.contract_template_version, template_version)
        self.assertEqual(document.order, 1)
        self.assertEqual(package_definition.documents.count(), 1)
        self.assertEqual(package_definition.documents.first(), document)

    def test_contract_package_fields(self):
        package_definition = self._create_package_definition()
        contract_package = self._create_contract_package(package_definition=package_definition)

        self.assertEqual(contract_package.package_definition, package_definition)
        self.assertEqual(contract_package.state, ContractPackage.State.DRAFT)
        self.assertEqual(contract_package.origination_key, "orig-123")
        self.assertIsNotNone(contract_package.created_at)
        self.assertIsNotNone(contract_package.updated_at)

    def test_contract_document_fields_and_relation(self):
        contract_package = self._create_contract_package()
        template_version = self._create_template_version()
        document = self._create_contract_document(
            contract_package=contract_package,
            contract_template_version=template_version,
        )

        self.assertEqual(document.contract_package, contract_package)
        self.assertEqual(document.contract_template_version, template_version)
        self.assertEqual(document.html_snapshot, "<html>Snapshot</html>")
        self.assertIsNotNone(document.created_at)
        self.assertEqual(contract_package.documents.count(), 1)
        self.assertEqual(contract_package.documents.first(), document)

    def test_contract_signature_fields(self):
        document = self._create_contract_document()
        signed_at = timezone.now()
        signature = ContractSignature.objects.create(
            contract_document=document,
            signer="Jane Doe",
            artifact="signature-bytes",
            signed_at=signed_at,
            ip_address="203.0.113.10",
            method="ESIGN",
        )

        self.assertEqual(signature.contract_document, document)
        self.assertEqual(signature.signer, "Jane Doe")
        self.assertEqual(signature.artifact, "signature-bytes")
        self.assertEqual(signature.signed_at, signed_at)
        self.assertEqual(signature.ip_address, "203.0.113.10")
        self.assertEqual(signature.method, "ESIGN")
        self.assertEqual(document.signatures.count(), 1)
        self.assertEqual(document.signatures.first(), signature)

    def test_contract_event_fields(self):
        contract_package = self._create_contract_package()
        event = ContractEvent.objects.create(
            contract_package=contract_package,
            event_type="GENERATED",
            actor="system",
            payload={"status": "generated"},
        )

        self.assertEqual(event.contract_package, contract_package)
        self.assertEqual(event.event_type, "GENERATED")
        self.assertEqual(event.actor, "system")
        self.assertEqual(event.payload, {"status": "generated"})
        self.assertIsNotNone(event.created_at)
        self.assertEqual(contract_package.events.count(), 1)
        self.assertEqual(contract_package.events.first(), event)

    def test_contract_attachment_fields(self):
        document = self._create_contract_document()
        attachment = ContractAttachment.objects.create(
            contract_document=document,
            external_uri="https://example.com/contract.pdf",
        )

        self.assertEqual(attachment.contract_document, document)
        self.assertIsNone(attachment.file)
        self.assertEqual(attachment.external_uri, "https://example.com/contract.pdf")
        self.assertIsNotNone(attachment.created_at)
        self.assertEqual(document.attachments.count(), 1)
        self.assertEqual(document.attachments.first(), attachment)

    def test_candidate_placement_fields(self):
        placement = CandidatePlacement.objects.create(
            candidate="Alex Candidate",
            candidate_email="alex@example.com",
            employer="Acme Corp",
            salary=Decimal("120000.00"),
            placement_fee=Decimal("18000.00"),
            start_date=date(2026, 1, 15),
            contract_package=None,
        )

        self.assertEqual(placement.candidate, "Alex Candidate")
        self.assertEqual(placement.candidate_email, "alex@example.com")
        self.assertEqual(placement.employer, "Acme Corp")
        self.assertEqual(placement.salary, Decimal("120000.00"))
        self.assertEqual(placement.placement_fee, Decimal("18000.00"))
        self.assertEqual(placement.start_date, date(2026, 1, 15))
        self.assertIsNone(placement.contract_package)
        self.assertIsNotNone(placement.created_at)
        self.assertIsNotNone(placement.updated_at)
