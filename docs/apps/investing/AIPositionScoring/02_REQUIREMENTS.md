# AI Position Scoring System - Requirements

## Functional Requirements

### 1. Position Fetching
- Fetch positions from OptionPlay API
- Fetch positions from Unusual Whales flow data
- Store in SuggestedPosition model

### 2. AI Scoring (6-Factor Algorithm)
- Historical win rate analysis
- IV rank assessment
- Greeks evaluation (delta, theta, gamma, vega)
- Risk/reward ratio calculation
- Earnings proximity check
- Liquidity analysis

### 3. Rating System
- Score range: 0-100
- Rating categories: Excellent (95+), Very Good (85+), Good (70+), Fair (50+), Poor (<50)
- Confidence levels: High, Medium, Low
- AI recommendation: Strong Buy, Buy, Hold, Avoid

## Technical Requirements
- RESTful API integration
- Database: PostgreSQL
- AI service: position_ranking_service.py
- Admin interface updates
- Staff UI enhancements

See: [Implementation Details](04_IMPLEMENTATION.md)

---
*Part of the AI Position Scoring System (Phase 9)*
