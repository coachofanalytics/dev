from django.core.management.base import BaseCommand
from datetime import date, timedelta
from decimal import Decimal
import random

from investing.models_investment_tracking import (
    IndividualInvestment,
    InvestmentPerformance,
)


class Command(BaseCommand):
    help = "Send monthly investment reports to all active individual investors"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without actually sending emails",
        )
        parser.add_argument(
            "--simulate-performance",
            action="store_true",
            help="Simulate performance data for testing",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        simulate = options["simulate_performance"]

        self.stdout.write("Starting monthly investment report process...")

        # Get all active individual investments
        active_investments = IndividualInvestment.objects.filter(
            status="active", monthly_reports=True
        )

        self.stdout.write(f"Found {active_investments.count()} active investments")

        for investment in active_investments:
            self.stdout.write(
                f"Processing investment for {investment.investor.get_full_name()}..."
            )

            if simulate:
                # Simulate performance data for testing
                self.simulate_performance_data(investment)

            # Check if we need to create a new performance record
            last_performance = investment.performance_records.first()

            if not last_performance or self.should_create_new_performance(
                last_performance
            ):
                if not dry_run:
                    # Create new performance record
                    self.create_performance_record(investment)

                    # Send monthly report
                    self.send_monthly_report(investment)

                    # Check for upgrade opportunities
                    self.check_upgrade_opportunities(investment)
                else:
                    self.stdout.write(
                        f"  [DRY RUN] Would send report to {investment.investor.email}"
                    )
            else:
                self.stdout.write("  Skipping - recent performance record exists")

        self.stdout.write("Monthly report process completed!")

    def should_create_new_performance(self, last_performance):
        """Check if we should create a new performance record"""
        # Create new record if last one is more than 25 days old
        days_since_last = (date.today() - last_performance.performance_date).days
        return days_since_last >= 25

    def simulate_performance_data(self, investment):
        """Simulate realistic performance data for testing"""
        last_performance = investment.performance_records.first()

        if last_performance:
            # Simulate growth based on expected return rate
            base_growth_rate = (
                investment.expected_return_rate / 100 / 12
            )  # Monthly rate
            volatility = 0.02  # 2% monthly volatility

            # Add some randomness
            random_factor = random.uniform(-volatility, volatility)
            monthly_return_rate = base_growth_rate + random_factor

            # Calculate new value
            new_value = last_performance.period_end_value * (1 + monthly_return_rate)

            # Update investment current value
            investment.update_current_value(new_value)

            self.stdout.write(f"  Simulated new value: ${new_value:.2f}")

    def create_performance_record(self, investment):
        """Create a new performance record"""
        last_performance = investment.performance_records.first()

        if last_performance:
            period_start = last_performance.period_end + timedelta(days=1)
        else:
            period_start = investment.investment_date

        period_end = date.today()

        # Calculate period return
        period_return = investment.current_value - (
            last_performance.period_end_value
            if last_performance
            else investment.investment_amount
        )
        period_return_percentage = (
            period_return
            / (
                last_performance.period_end_value
                if last_performance
                else investment.investment_amount
            )
        ) * 100

        # Simulate business metrics (in real implementation, these would come from actual business data)
        revenue_generated = Decimal(random.uniform(5000, 15000))
        expenses_incurred = Decimal(random.uniform(3000, 8000))
        net_profit = revenue_generated - expenses_incurred

        InvestmentPerformance.objects.create(
            investment=investment,
            period_start=period_start,
            period_end=period_end,
            period_start_value=(
                last_performance.period_end_value
                if last_performance
                else investment.investment_amount
            ),
            period_end_value=investment.current_value,
            period_return=period_return,
            period_return_percentage=period_return_percentage,
            revenue_generated=revenue_generated,
            expenses_incurred=expenses_incurred,
            net_profit=net_profit,
            key_achievements="Successfully launched new product features and acquired 50+ new customers this month.",
            challenges_faced="Faced increased competition in the market, but maintained strong customer retention.",
            next_period_goals="Focus on expanding into new markets and improving operational efficiency.",
        )

        self.stdout.write(
            f"  Created performance record for {period_start} to {period_end}"
        )

    def send_monthly_report(self, investment):
        """Send monthly report to investor"""
        from investing.views_investment_tracking import send_monthly_investment_report

        try:
            send_monthly_investment_report(investment)
            self.stdout.write(f"  Sent monthly report to {investment.investor.email}")
        except Exception as e:
            self.stdout.write(f"  Error sending report: {str(e)}")

    def check_upgrade_opportunities(self, investment):
        """Check for upgrade opportunities"""
        from investing.views_investment_tracking import check_upgrade_opportunities

        try:
            check_upgrade_opportunities(investment)
            self.stdout.write("  Checked upgrade opportunities")
        except Exception as e:
            self.stdout.write(f"  Error checking upgrades: {str(e)}")
