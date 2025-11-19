from django.core.management.base import BaseCommand
from django.utils import timezone

from ...services.optionplay_outcome_service import OptionPlayOutcomeService


class Command(BaseCommand):
    help = "Evaluate historical outcomes for expired OptionPlay / UW suggestions."

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help="As-of date (YYYY-MM-DD). Defaults to today."
        )

    def handle(self, *args, **options):
        service = OptionPlayOutcomeService()

        as_of = timezone.now().date()
        if options.get('date'):
            try:
                as_of = timezone.datetime.strptime(options['date'], "%Y-%m-%d").date()
            except ValueError:
                self.stderr.write(self.style.ERROR("Invalid --date format. Use YYYY-MM-DD."))
                return

        summary = service.evaluate_pending(as_of=as_of)
        self.stdout.write(self.style.SUCCESS(
            f"Evaluated {summary['evaluated']} suggestions "
            f"(created {summary['created']}, unsupported {summary['unsupported']}, errors {summary['errors']})."
        ))





