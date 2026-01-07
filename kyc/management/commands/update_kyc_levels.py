"""
Management command to update KYC verification levels for users with approved documents.
Run this to fix any users who were approved before the auto-update was implemented.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from kyc.models import KYCDocument, KYCVerificationLevel

User = get_user_model()


class Command(BaseCommand):
    help = 'Update KYC verification levels for users with approved documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get all approved documents
        approved_docs = KYCDocument.objects.filter(status='approved').select_related('user')

        users_to_update = {}

        for doc in approved_docs:
            user = doc.user
            if user.id not in users_to_update:
                users_to_update[user.id] = {
                    'user': user,
                    'identity': False,
                    'address': False,
                    'business': False,
                }

            # Track which verifications this user should have
            if doc.document_type in ['national_id', 'passport', 'drivers_license']:
                users_to_update[user.id]['identity'] = True
            elif doc.document_type == 'proof_of_address':
                users_to_update[user.id]['address'] = True
            elif doc.document_type == 'business_registration':
                users_to_update[user.id]['business'] = True

        updated_count = 0
        created_count = 0

        for user_data in users_to_update.values():
            user = user_data['user']

            # Get or create verification level
            level, created = KYCVerificationLevel.objects.get_or_create(user=user)

            if created:
                created_count += 1
                self.stdout.write(f'Created KYCVerificationLevel for {user.username}')

            # Check if we need to update
            needs_update = False
            changes = []

            if user_data['identity'] and not level.identity_verified:
                needs_update = True
                changes.append('identity_verified')
                if not dry_run:
                    level.identity_verified = True

            if user_data['address'] and not level.address_verified:
                needs_update = True
                changes.append('address_verified')
                if not dry_run:
                    level.address_verified = True

            if user_data['business'] and not level.business_verified:
                needs_update = True
                changes.append('business_verified')
                if not dry_run:
                    level.business_verified = True

            if needs_update:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"[DRY RUN] Would update" if dry_run else "Updated"} {user.username}: {", ".join(changes)}'
                    )
                )

                if not dry_run:
                    # Recalculate verification level
                    level.update_level()
                    self.stdout.write(f'  New level: {level.get_level_display()}')

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n{"DRY RUN " if dry_run else ""}Summary:'))
        self.stdout.write(f'- KYCVerificationLevels created: {created_count}')
        self.stdout.write(f'- Users updated: {updated_count}')
        self.stdout.write(f'- Total approved documents processed: {approved_docs.count()}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nRun without --dry-run to apply changes'))
