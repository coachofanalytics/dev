"""Quick UAT test script for AI scoring"""
from investing.models import SuggestedPosition

total = SuggestedPosition.objects.count()
scored = SuggestedPosition.objects.filter(ai_score__isnull=False).count()

print(f"=" * 60)
print(f"UAT AI SCORING VERIFICATION")
print(f"=" * 60)
print(f"Total Positions: {total}")
print(f"AI Scored: {scored}")
print(f"Percentage: {scored/total*100:.1f}%" if total > 0 else "N/A")
print(f"=" * 60)

if scored > 0:
    # Score distribution
    excellent = SuggestedPosition.objects.filter(ai_rating='EXCELLENT').count()
    good = SuggestedPosition.objects.filter(ai_rating='GOOD').count()
    average = SuggestedPosition.objects.filter(ai_rating='AVERAGE').count()
    below_avg = SuggestedPosition.objects.filter(ai_rating='BELOW_AVERAGE').count()
    poor = SuggestedPosition.objects.filter(ai_rating='POOR').count()
    
    print(f"\nSCORE DISTRIBUTION:")
    print(f"  EXCELLENT (95+):    {excellent:3} ({excellent/scored*100:5.1f}%)")
    print(f"  GOOD (85-94):       {good:3} ({good/scored*100:5.1f}%)")
    print(f"  AVERAGE (70-84):    {average:3} ({average/scored*100:5.1f}%)")
    print(f"  BELOW_AVG (50-69):  {below_avg:3} ({below_avg/scored*100:5.1f}%)")
    print(f"  POOR (0-49):        {poor:3} ({poor/scored*100:5.1f}%)")
    
    # Top 5
    top_5 = SuggestedPosition.objects.filter(ai_score__isnull=False).order_by('-ai_score')[:5]
    print(f"\nTOP 5 SCORED POSITIONS:")
    for i, pos in enumerate(top_5, 1):
        print(f"  {i}. {pos.symbol:6} Score: {pos.ai_score:5.1f}/100 ({pos.ai_rating})")
    
    print(f"\n" + "=" * 60)
    print(f"✅ AI SCORING WORKING ON UAT!")
    print(f"=" * 60)

