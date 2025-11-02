"""
Verify AI Scoring on UAT
Quick verification script for deployment

Usage:
    heroku run "cd coda && python manage.py verify_ai_scoring_uat" --app codamakutano

Author: CODA Development Team
Created: November 2, 2025
"""

from django.core.management.base import BaseCommand
from investing.models import SuggestedPosition


class Command(BaseCommand):
    help = 'Verify AI scoring is working on UAT'
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("🤖 UAT AI SCORING VERIFICATION"))
        self.stdout.write("=" * 70)
        
        total = SuggestedPosition.objects.count()
        scored = SuggestedPosition.objects.filter(ai_score__isnull=False).count()
        
        self.stdout.write(f"\n📊 DATA STATUS:")
        self.stdout.write(f"  Total Positions: {total}")
        self.stdout.write(f"  AI Scored: {scored}")
        if total > 0:
            self.stdout.write(f"  Percentage: {scored/total*100:.1f}%")
        
        if scored == 0:
            self.stdout.write(self.style.WARNING("\n⚠️  No AI-scored positions found!"))
            self.stdout.write("\nTo score positions, run:")
            self.stdout.write("  python manage.py test_ai_scoring_integration --count 10")
            return
        
        # Score distribution
        excellent = SuggestedPosition.objects.filter(ai_rating='EXCELLENT').count()
        good = SuggestedPosition.objects.filter(ai_rating='GOOD').count()
        average = SuggestedPosition.objects.filter(ai_rating='AVERAGE').count()
        below_avg = SuggestedPosition.objects.filter(ai_rating='BELOW_AVERAGE').count()
        poor = SuggestedPosition.objects.filter(ai_rating='POOR').count()
        
        self.stdout.write(f"\n🏆 SCORE DISTRIBUTION:")
        self.stdout.write(f"  EXCELLENT (95+):    {excellent:3} ({excellent/scored*100:5.1f}%) ⭐⭐⭐⭐⭐")
        self.stdout.write(f"  GOOD (85-94):       {good:3} ({good/scored*100:5.1f}%) ⭐⭐⭐⭐")
        self.stdout.write(f"  AVERAGE (70-84):    {average:3} ({average/scored*100:5.1f}%) ⭐⭐⭐")
        self.stdout.write(f"  BELOW_AVG (50-69):  {below_avg:3} ({below_avg/scored*100:5.1f}%) ⭐⭐")
        self.stdout.write(f"  POOR (0-49):        {poor:3} ({poor/scored*100:5.1f}%) ⭐")
        
        # Top 5
        top_5 = SuggestedPosition.objects.filter(ai_score__isnull=False).order_by('-ai_score')[:5]
        self.stdout.write(f"\n🥇 TOP 5 SCORED POSITIONS:")
        for i, pos in enumerate(top_5, 1):
            stars = "⭐" * min(5, int(pos.ai_score / 20))
            self.stdout.write(f"  {i}. {pos.symbol:6} {pos.ai_score:5.1f}/100 ({pos.ai_rating:15}) {stars}")
        
        # Bottom 5
        bottom_5 = SuggestedPosition.objects.filter(ai_score__isnull=False).order_by('ai_score')[:5]
        self.stdout.write(f"\n🔻 BOTTOM 5 (Should be rejected):")
        for i, pos in enumerate(bottom_5, 1):
            self.stdout.write(f"  {i}. {pos.symbol:6} {pos.ai_score:5.1f}/100 ({pos.ai_rating:15})")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ AI SCORING VERIFIED ON UAT!"))
        self.stdout.write("=" * 70)
        
        self.stdout.write("\n📋 NEXT STEPS:")
        self.stdout.write("  1. Check UI: /investing/managed/staff/suggestions/")
        self.stdout.write("  2. Verify star ratings display correctly")
        self.stdout.write("  3. Check position detail page for AI breakdown")
        self.stdout.write("  4. Test admin interface sorting/filtering")
        self.stdout.write("\n")

