# AI Position Scoring System - Implementation

## Services Implemented

### PositionRankingService
**Location:** `coda/investing/services/position_ranking_service.py`

**Key Methods:**
- `calculate_ai_score()` - Main scoring algorithm
- `_calculate_factor_scores()` - Individual factor scoring
- `_get_ai_rating()` - Convert score to rating
- `_get_confidence_level()` - Determine confidence
- `_generate_recommendation()` - Generate buy/hold/avoid

### Position Fetching
**Location:** `coda/investing/services/position_fetcher_service.py`

**Integration:**
- Fetches from OptionPlay
- Fetches from Unusual Whales
- Stores in `SuggestedPosition`
- Triggers AI scoring

## Database Changes

### Migration: `investing.0009_add_ai_scoring_fields`
Added fields:
- `ai_score`
- `ai_rating`
- `ai_confidence_level`
- `ai_recommendation`
- `ai_breakdown`

## Admin Interface
**File:** `investing/admin.py`

**Updates:**
- Added `ai_score_display()` method with star ratings
- Color-coded scores (green/blue/yellow/orange/red)
- Ordered by `ai_score` DESC by default
- Added AI filter in list_filter

## Staff UI
**Template:** `investing/staff/suggested_positions.html`

**Features:**
- Top 5 recommended section (ai_score >= 85)
- Star ratings display
- Color-coded confidence levels
- Sortable by AI score

See: [Scraper Setup Guide](references/SCRAPER_SETUP_GUIDE.md)
See: [Position Fetching Integration](references/POSITION_FETCHING_INTEGRATION.md)

---
*Part of the AI Position Scoring System (Phase 9)*
