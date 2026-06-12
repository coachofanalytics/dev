from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import (
    CandidatePlacement,
    ContractAttachment,
    ContractPackage,
    ContractTemplate,
    ContractTemplateVersion,
    PackageDefinition,
    PackageDefinitionDocument,
)
from main.services.contract_origination import origination as origination_service
from main.services.contract_origination import signature_service


class Command(BaseCommand):
    help = "Seed COP contract data"

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            template = self._get_or_create_template(
                name="Placement Agreement",
                slug="placement_agreement",
                body=(
                    "<h1>Placement Agreement</h1>"
                    "<p>Candidate: {{ candidate_name }}</p>"
                    "<p>Employer: {{ company_name }}</p>"
                    "<p>Salary: {{ salary }}</p>"
                    "<p>Placement Fee: {{ placement_fee }}</p>"
                    "<p>Start Date: {{ start_date }}</p>"
                ),
            )
            addendum = self._get_or_create_template(
                name="Placement Addendum",
                slug="placement_addendum",
                body=(
                    "<h2>Placement Addendum</h2>"
                    "<p>Candidate: {{ candidate_name }}</p>"
                    "<p>Employer: {{ company_name }}</p>"
                ),
            )

            package_definition = self._get_or_create_package_definition()
            if not package_definition.documents.exists():
                PackageDefinitionDocument.objects.create(
                    package_definition=package_definition,
                    contract_template_version=template,
                    order=1,
                )
                PackageDefinitionDocument.objects.create(
                    package_definition=package_definition,
                    contract_template_version=addendum,
                    order=2,
                )

            placement_generated = self._get_or_create_placement(
                candidate="Alice Candidate",
                candidate_email="alice@example.com",
                employer="Acme Corp",
                salary=Decimal("120000.00"),
                placement_fee=Decimal("18000.00"),
                start_date=date(2026, 6, 1),
            )
            placement_executed = self._get_or_create_placement(
                candidate="Jordan Smith",
                candidate_email="jordan@example.com",
                employer="Global Ventures",
                salary=Decimal("98000.00"),
                placement_fee=Decimal("14700.00"),
                start_date=date(2026, 7, 1),
            )

            generated_package = self._ensure_originated(placement_generated)
            executed_package = self._ensure_originated(placement_executed)

            self._ensure_signed(executed_package, placement_executed.candidate)
            self._ensure_attachment(executed_package)

        self.stdout.write(self.style.SUCCESS("COP seed data created."))

    def _get_or_create_template(self, name, slug, body):
        contract_template, _ = ContractTemplate.objects.get_or_create(
            slug=slug,
            defaults={"name": name},
        )
        version, _ = ContractTemplateVersion.objects.get_or_create(
            contract_template=contract_template,
            version=1,
            defaults={
                "template_body": body,
                "is_published": True,
            },
        )
        if not version.is_published:
            version.is_published = True
            version.save(update_fields=["is_published"])
        return version

    def _get_or_create_package_definition(self):
        package_definition, _ = PackageDefinition.objects.get_or_create(
            slug="placement_standard_v1",
            defaults={
                "name": "Placement Standard v1",
                "merge_schema": {
                    "required_fields": [
                        "candidate_name",
                        "company_name",
                        "salary",
                        "placement_fee",
                        "start_date",
                    ]
                },
            },
        )
        if not package_definition.merge_schema:
            package_definition.merge_schema = {
                "required_fields": [
                    "candidate_name",
                    "company_name",
                    "salary",
                    "placement_fee",
                    "start_date",
                ]
            }
            package_definition.save(update_fields=["merge_schema"])
        return package_definition

    def _get_or_create_placement(
        self,
        candidate,
        candidate_email,
        employer,
        salary,
        placement_fee,
        start_date,
    ):
        placement, _ = CandidatePlacement.objects.update_or_create(
            candidate=candidate,
            employer=employer,
            start_date=start_date,
            defaults={
                "candidate_email": candidate_email,
                "salary": salary,
                "placement_fee": placement_fee,
            },
        )
        return placement

    def _ensure_originated(self, placement):
        if placement.contract_package:
            return placement.contract_package
        return origination_service.create_from_placement(placement.id)

    def _ensure_signed(self, contract_package, signer_name):
        if contract_package.state == ContractPackage.State.GENERATED:
            signature_service.mark_package_sent(contract_package, actor="system")

        if contract_package.state != ContractPackage.State.SENT:
            return

        token = signature_service.generate_package_signing_token(contract_package)
        signature_service.sign_package(
            token=token,
            signer_name=signer_name,
            ip_address="203.0.113.10",
            method="SEED",
        )

    def _ensure_attachment(self, contract_package):
        if not contract_package.documents.exists():
            return

        document = contract_package.documents.first()
        if ContractAttachment.objects.filter(contract_document=document).exists():
            return

        ContractAttachment.objects.create(
            contract_document=document,
            external_uri="https://example.com/sample-attachment.pdf",
        )
