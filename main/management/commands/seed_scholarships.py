from django.core.management.base import BaseCommand
from main.create_scholarship_data import create_readable_scholarships, create_targeted_scholarships, create_bulk_scholarships_with_currency_mix

class Command(BaseCommand):
    help = 'Seed Scholarships data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating readable scholarships...')
        create_readable_scholarships(50)

        self.stdout.write('Creating targeted scholarships...')
        create_targeted_scholarships()

        self.stdout.write('Creating bulk scholarships with currency mix...')
        create_bulk_scholarships_with_currency_mix(100)

        self.stdout.write(self.style.SUCCESS('Scholarships seeded successfully'))