
from django.core.management.base import BaseCommand
from main.create_training_data import (
    create_training_courses, create_targeted_courses,
    create_bulk_training_courses, print_course_stats, fix_enrollment_statuses
)

class Command(BaseCommand):
    help = 'Seed Training Courses data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating training courses...')
        create_training_courses(50)

        self.stdout.write('Creating targeted courses...')
        create_targeted_courses()

        self.stdout.write('Creating bulk training courses...')
        create_bulk_training_courses(60)

        self.stdout.write('Printing course stats...')
        print_course_stats()

        self.stdout.write('Fixing enrollment statuses...')
        fix_enrollment_statuses()

        self.stdout.write(self.style.SUCCESS('Training courses seeded successfully'))