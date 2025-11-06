import time
from django.test import TestCase
from decimal import Decimal

from main.models import Donation_organization


class DonationOrganizationPerformanceTests(TestCase):
	"""Lightweight performance checks for Donation_organization model.

	These tests are intentionally conservative: they verify correct behavior
	and capture timing information, but do not enforce strict timing
	assertions that would be flaky across environments. If you want strong
	performance gates, set environment-specific thresholds and assert them.
	"""

	def test_bulk_create_performance(self):
		"""Measure time to bulk_create N donation records and assert they were created."""
		N = 500
		objs = []
		for i in range(N):
			objs.append(Donation_organization(
				donor_name=f'Donor {i}',
				email=f'donor{i}@example.test',
				amount=Decimal('10.00'),
				message='performance test',
			))

		start = time.perf_counter()
		Donation_organization.objects.bulk_create(objs)
		elapsed = time.perf_counter() - start

		created = Donation_organization.objects.count()

		# Basic correctness assertion
		self.assertEqual(created, N, f'Expected {N} donations after bulk_create, got {created}')

		# Emit timing info to the test output so it's visible in CI logs
		print(f"bulk_create of {N} Donation_organization objects took {elapsed:.3f}s")

	def test_individual_create_latency(self):
		"""Measure average time to create single records (not enforced).

		This is useful to get a sense of latency when not using bulk operations.
		"""
		N = 50
		start = time.perf_counter()
		for i in range(N):
			Donation_organization.objects.create(
				donor_name=f'Ind Donor {i}',
				email=f'ind{i}@example.test',
				amount=Decimal('5.00'),
				message='single insert',
			)
		elapsed = time.perf_counter() - start
		avg = elapsed / N
		print(f"Average individual insert time over {N} inserts: {avg:.4f}s (total {elapsed:.3f}s)")
		self.assertEqual(Donation_organization.objects.count(), N + 0)  # sanity check
