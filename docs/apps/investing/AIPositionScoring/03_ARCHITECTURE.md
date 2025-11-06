# AI Position Scoring System - Architecture

## System Components

### 1. Position Ranking Service
**File:** `investing/services/position_ranking_service.py`

**Responsibilities:**
- 6-factor scoring algorithm
- Historical data analysis
- AI recommendation generation

### 2. Data Models
**Model:** `SuggestedPosition`

**New Fields:**
- `ai_score` (Decimal 0-100)
- `ai_rating` (Excellent/Very Good/Good/Fair/Poor)
- `ai_confidence_level` (High/Medium/Low)
- `ai_recommendation` (Strong Buy/Buy/Hold/Avoid)
- `ai_breakdown` (JSON with factor scores)

### 3. Integration Points
- OptionPlay API
- Unusual Whales API
- Position Fetcher Service
- Admin Interface
- Staff Dashboard

## Data Flow
1. Fetch positions from APIs
2. Store in SuggestedPosition
3. Run AI scoring algorithm
4. Update model with scores
5. Display in admin/staff UI
6. Sort by score (highest first)

See: [Implementation Guide](04_IMPLEMENTATION.md)

---
*Part of the AI Position Scoring System (Phase 9)*
