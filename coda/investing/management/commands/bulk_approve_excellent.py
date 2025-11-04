"""
Management command to bulk-approve EXCELLENT positions

Usage:
    python manage.py bulk_approve_excellent

This command finds all pending SuggestedPositions with:
- review_status = 'pending'
- ai_score >= 60 (ABOVE_AVERAGE or better)
- ai_rating in ['EXCELLENT', 'GOOD', 'AVERAGE']

And automatically approves them.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from investing.models import SuggestedPosition
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Bulk approve EXCELLENT positions currently in pending review'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-score',
            type=int,
            default=95,
            help='Minimum AI score for auto-approval (default: 95 = EXCELLENT only)'
        )
        parser.add_argument(
            '--top-n',
            type=int,
            default=6,
            help='Number of top positions to distribute to accounts (default: 6)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be approved without actually approving'
        )
        parser.add_argument(
            '--staff-user',
            type=str,
            help='Username of staff user to attribute approvals to (defaults to first superuser)'
        )

    def handle(self, *args, **options):
        min_score = options['min_score']
        top_n = options['top_n']
        dry_run = options['dry_run']
        staff_username = options.get('staff_user')
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🤖 BULK APPROVE EXCELLENT POSITIONS + DISTRIBUTE"))
        self.stdout.write("=" * 80)
        
        # Get staff user
        if staff_username:
            try:
                staff_user = User.objects.get(username=staff_username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ User '{staff_username}' not found"))
                return
        else:
            staff_user = User.objects.filter(is_superuser=True).first()
            if not staff_user:
                self.stdout.write(self.style.ERROR("❌ No superuser found. Please specify --staff-user"))
                return
        
        self.stdout.write(f"👤 Staff User: {staff_user.username}")
        self.stdout.write(f"📏 Min Score: {min_score} (EXCELLENT only)")
        self.stdout.write(f"📊 Top N for Distribution: {top_n} positions")
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY RUN MODE - No changes will be made"))
        self.stdout.write("")
        
        # Find pending positions with score >= threshold
        pending_positions = SuggestedPosition.objects.filter(
            review_status='pending',
            ai_score__gte=min_score
        ).order_by('-ai_score')
        
        total_count = pending_positions.count()
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING(f"ℹ️  No pending positions found with score ≥{min_score}"))
            return
        
        self.stdout.write(f"📊 Found {total_count} positions eligible for auto-approval:")
        self.stdout.write("")
        
        # Show breakdown by rating
        excellent = pending_positions.filter(ai_rating='EXCELLENT').count()
        good = pending_positions.filter(ai_rating='GOOD').count()
        average = pending_positions.filter(ai_rating='AVERAGE').count()
        below_avg = pending_positions.filter(ai_rating='BELOW_AVERAGE').count()
        
        self.stdout.write(f"  🌟 EXCELLENT: {excellent}")
        self.stdout.write(f"  ✅ GOOD: {good}")
        self.stdout.write(f"  🟡 AVERAGE: {average}")
        self.stdout.write(f"  ⚠️  BELOW_AVERAGE: {below_avg}")
        self.stdout.write("")
        
        # Show positions that will be approved
        self.stdout.write("Positions to approve:")
        self.stdout.write("-" * 80)
        
        approved_count = 0
        for idx, pos in enumerate(pending_positions, 1):
            rating_emoji = {
                'EXCELLENT': '🌟',
                'GOOD': '✅',
                'AVERAGE': '🟡',
                'BELOW_AVERAGE': '⚠️',
            }.get(pos.ai_rating, '❓')
            
            self.stdout.write(
                f"{idx:2d}. {rating_emoji} {pos.symbol:6s} {pos.strategy:20s} "
                f"Score: {pos.ai_score:5.1f}/100 ({pos.ai_rating or 'N/A':15s}) "
                f"Premium: ${pos.premium_collected or 0:6.0f}"
            )
            
            if not dry_run:
                # Approve the position
                try:
                    pos.approve(
                        staff_user=staff_user,
                        notes=f"Bulk auto-approved: AI Score {pos.ai_score:.1f}/100 ({pos.ai_rating}) exceeds threshold of {min_score}"
                    )
                    approved_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ Error approving {pos.symbol}: {e}"))
        
        self.stdout.write("-" * 80)
        self.stdout.write("")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f"⚠️  DRY RUN: Would approve {total_count} positions"))
            self.stdout.write(f"⚠️  DRY RUN: Would distribute top {top_n} to client accounts")
            self.stdout.write("Run without --dry-run to actually approve and distribute")
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully approved {approved_count}/{total_count} positions!"))
            
            # Now distribute top N to client accounts
            self.stdout.write("")
            self.stdout.write("=" * 80)
            self.stdout.write("📦 AUTO-DISTRIBUTING TOP POSITIONS TO CLIENT ACCOUNTS")
            self.stdout.write("=" * 80)
            
            from investing.services.auto_approval_service import AutoApprovalService
            auto_service = AutoApprovalService()
            
            # Get approved positions, sorted by score
            approved_positions = SuggestedPosition.objects.filter(
                review_status='approved',
                ai_score__gte=min_score
            ).order_by('-ai_score')[:top_n]
            
            approved_ids = [p.id for p in approved_positions]
            
            if approved_ids:
                self.stdout.write(f"📊 Distributing top {len(approved_ids)} positions to client accounts...")
                
                try:
                    # Run distribution only (positions already approved)
                    distribution_result = auto_service._distribute_to_accounts(
                        approved_suggestions=list(approved_positions),
                        created_by=staff_user
                    )
                    
                    distributed_count = distribution_result.get('total_distributed', 0)
                    batch_count = distribution_result.get('batch_count', 0)
                    
                    self.stdout.write(self.style.SUCCESS(f"✅ Distributed {distributed_count} positions to {batch_count} accounts"))
                    
                    # Show batch details
                    for account_id, positions in distribution_result.get('distributions', {}).items():
                        self.stdout.write(f"  📦 Account #{account_id}: {len(positions)} positions assigned")
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Distribution error: {e}"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  No approved positions to distribute"))
            
            # Show updated counts
            pending_remaining = SuggestedPosition.objects.filter(review_status='pending').count()
            approved_total = SuggestedPosition.objects.filter(review_status='approved').count()
            
            self.stdout.write("")
            self.stdout.write(f"📊 Final Status:")
            self.stdout.write(f"  ⏳ Pending Review: {pending_remaining}")
            self.stdout.write(f"  ✅ Approved: {approved_total}")
        
        self.stdout.write("")
        self.stdout.write("=" * 80)

