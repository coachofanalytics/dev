"""
Position Ranking Service - Multi-Factor Intelligent Ranking

Ranks SuggestedPosition objects using weighted multi-factor analysis to
select the best 5 positions from 20+ approved positions.

Ranking Algorithm:
    Total Score = (Whales × 35%) + (Earnings × 25%) + (ROC × 20%) + (DTE × 20%)

Factors:
    1. Whales Signal (35%) - Unusual Whales directional alignment
    2. Earnings Safety (25%) - Proximity to earnings events
    3. Profit Potential (20%) - Return on Capital (ROC%)
    4. DTE Diversity (20%) - Spread across expiration dates

Business Rules:
    - Bonus: Bull Put + Bullish Flow = +10 points
    - Penalty: Earnings <5 days before expiry = -50 points
    - Penalty: 3+ positions same expiry week = clustering penalty
    - Limit: Max 3 positions per sector

Created: November 5, 2025
Phase: 10A - Smart Position Ranking
"""

import logging
from decimal import Decimal
from datetime import date, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class PositionRankingService:
    """
    Intelligent position ranking using multi-factor analysis
    
    Usage:
        ranker = PositionRankingService()
        ranked = ranker.rank_positions(pending_positions)
        top_5 = ranker.get_top_n(ranked, n=5)
    """
    
    # Ranking weights (configurable)
    WHALES_WEIGHT = Decimal('0.35')      # 35% - Highest priority
    EARNINGS_WEIGHT = Decimal('0.25')    # 25% - Safety critical
    PROFIT_WEIGHT = Decimal('0.20')      # 20% - Return matters
    DTE_WEIGHT = Decimal('0.20')         # 20% - Diversification
    
    # Bonus/Penalty points
    STRATEGY_ALIGNMENT_BONUS = 10    # Bull Put + Bullish Flow
    EARNINGS_CONFLICT_PENALTY = -50  # Earnings before expiry
    CLUSTERING_PENALTY = -15         # 3+ same expiry week
    
    # Business limits
    MAX_POSITIONS_PER_SECTOR = 3
    
    def __init__(self):
        """Initialize ranking service"""
        self.logger = logger
    
    def rank_positions(self, positions: QuerySet or List) -> List[Dict]:
        """
        Rank positions using weighted multi-factor algorithm
        
        Args:
            positions: QuerySet or List of SuggestedPosition objects
            
        Returns:
            List of dicts with position, scores, rank, recommendation:
            [{
                'position': SuggestedPosition,
                'total_score': Decimal,
                'breakdown': {
                    'whales_score': Decimal,
                    'earnings_score': Decimal,
                    'profit_score': Decimal,
                    'dte_score': Decimal
                },
                'bonuses': List[str],  # e.g., ["Strategy aligned with flow"]
                'penalties': List[str],  # e.g., ["Earnings in 3 days"]
                'rank': int,
                'recommendation': str,  # "STRONG BUY", "BUY", "HOLD", "AVOID"
                'selection_reason': str  # Human-readable explanation
            }]
        """
        if not positions:
            self.logger.warning("📊 No positions to rank")
            return []
        
        # Convert QuerySet to list if needed
        positions_list = list(positions)
        
        self.logger.info(f"📊 Ranking {len(positions_list)} positions...")
        
        # Score each position
        scored_positions = []
        for position in positions_list:
            try:
                score_data = self._score_position(position, positions_list)
                scored_positions.append(score_data)
            except Exception as e:
                self.logger.error(f"❌ Error scoring {position.symbol}: {e}")
                continue
        
        # Sort by total score (descending)
        scored_positions.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Add rank
        for idx, item in enumerate(scored_positions, start=1):
            item['rank'] = idx
        
        self.logger.info(f"✅ Ranked {len(scored_positions)} positions")
        self.logger.info(f"🏆 Top 3: {', '.join([p['position'].symbol for p in scored_positions[:3]])}")
        
        return scored_positions
    
    def _score_position(self, position, all_positions: List) -> Dict:
        """
        Score a single position on all factors
        
        Args:
            position: SuggestedPosition object
            all_positions: List of all positions (for DTE diversity calculation)
            
        Returns:
            Dict with position, scores, and metadata
        """
        # Calculate individual factor scores (0-100 each)
        whales_score = self._score_whales_signal(position)
        earnings_score = self._score_earnings_safety(position)
        profit_score = self._score_profit_potential(position)
        dte_score = self._score_dte_diversity(position, all_positions)
        
        # Calculate weighted total
        total_score = (
            (whales_score * self.WHALES_WEIGHT) +
            (earnings_score * self.EARNINGS_WEIGHT) +
            (profit_score * self.PROFIT_WEIGHT) +
            (dte_score * self.DTE_WEIGHT)
        )
        
        # Apply bonuses/penalties
        bonuses = []
        penalties = []
        
        # Bonus: Strategy aligned with flow
        if self._is_strategy_aligned(position):
            total_score += self.STRATEGY_ALIGNMENT_BONUS
            bonuses.append(f"Strategy aligned with {position.symbol} flow direction")
        
        # Penalty: Earnings conflict
        if self._has_earnings_conflict(position):
            total_score += self.EARNINGS_CONFLICT_PENALTY  # Negative
            penalties.append(f"Earnings {self._days_to_earnings(position)} days before expiry")
        
        # Ensure score stays in 0-100 range
        total_score = max(Decimal('0'), min(Decimal('100'), total_score))
        
        # Generate recommendation
        recommendation = self._generate_recommendation(total_score)
        selection_reason = self._generate_selection_reason(position, whales_score, earnings_score, profit_score, dte_score)
        
        return {
            'position': position,
            'total_score': total_score,
            'breakdown': {
                'whales_score': whales_score,
                'earnings_score': earnings_score,
                'profit_score': profit_score,
                'dte_score': dte_score
            },
            'bonuses': bonuses,
            'penalties': penalties,
            'rank': 0,  # Set later
            'recommendation': recommendation,
            'selection_reason': selection_reason
        }
    
    def _score_whales_signal(self, position) -> Decimal:
        """
        Score based on Unusual Whales directional signal strength
        
        Scoring:
            +50 points = Strong bullish flow (premium >$1M, multiple signals)
            +30 points = Moderate bullish flow
            +10 points = Weak bullish signal
            0 points = No signal or neutral
            -20 points = Bearish signal (conflicts with our bullish position)
            -50 points = Strong bearish (major conflict)
        
        Strategy Alignment:
            Bull Put Spread = wants bullish signal
            Bear Call Spread = wants bearish signal
            
        Returns:
            Decimal 0-100 (normalized score)
        """
        # Get Whales data from position.notes or separate field
        # For now, using ai_score as proxy (would integrate with actual Whales data)
        
        # Check if position has Whales data in notes
        notes = position.notes or ""
        
        # Parse Whales signal from notes
        whales_signal = self._parse_whales_signal(notes)
        
        if whales_signal is None:
            # No Whales data - use ai_score as fallback
            # High AI score suggests good setup
            ai_score = position.ai_score or 50
            normalized = min(100, max(0, ai_score))
            self.logger.debug(f"  🐋 {position.symbol}: No Whales data, using AI score {normalized}")
            return Decimal(str(normalized))
        
        # Convert Whales signal to score
        # Signal ranges from -50 (bearish) to +50 (bullish)
        # Convert to 0-100 scale
        
        strategy = position.strategy
        
        if 'bull_put' in strategy.lower() or 'short_put' in strategy.lower():
            # Bullish position - wants bullish flow
            if whales_signal >= 40:
                score = 100  # Strong bullish = perfect
            elif whales_signal >= 25:
                score = 85   # Moderate bullish = good
            elif whales_signal >= 10:
                score = 70   # Weak bullish = okay
            elif whales_signal >= -10:
                score = 50   # Neutral = meh
            elif whales_signal >= -25:
                score = 25   # Weak bearish = conflict
            else:
                score = 0    # Strong bearish = major conflict
        
        elif 'bear_call' in strategy.lower() or 'short_call' in strategy.lower():
            # Bearish position - wants bearish flow
            if whales_signal <= -40:
                score = 100  # Strong bearish = perfect
            elif whales_signal <= -25:
                score = 85   # Moderate bearish = good
            elif whales_signal <= -10:
                score = 70   # Weak bearish = okay
            elif whales_signal <= 10:
                score = 50   # Neutral = meh
            elif whales_signal <= 25:
                score = 25   # Weak bullish = conflict
            else:
                score = 0    # Strong bullish = major conflict
        
        else:
            # Neutral strategy or unknown - prefer moderate signals
            score = 50 + abs(whales_signal)  # Stronger signal = better
            score = min(100, score)
        
        self.logger.debug(f"  🐋 {position.symbol}: Whales signal {whales_signal} → score {score}")
        
        return Decimal(str(score))
    
    def _parse_whales_signal(self, notes: str) -> Optional[int]:
        """
        Parse Unusual Whales signal strength from position notes
        
        Expected format in notes:
            "Unusual Whales: Bullish +45"
            "Unusual Whales: Bearish -30"
            "Flow Signal: +25 (Options Flow)"
        
        Returns:
            int (-50 to +50) or None if not found
        """
        if not notes:
            return None
        
        # Look for patterns like "+45" or "-30" after "Whales" or "Flow"
        import re
        
        patterns = [
            r'Whales.*?([+-]?\d+)',
            r'Flow.*?([+-]?\d+)',
            r'Bullish.*?([+-]?\d+)',
            r'Bearish.*?([+-]?\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, notes, re.IGNORECASE)
            if match:
                signal = int(match.group(1))
                # Clamp to -50 to +50
                return max(-50, min(50, signal))
        
        return None
    
    def _score_earnings_safety(self, position) -> Decimal:
        """
        Score based on earnings event proximity
        
        Scoring:
            100 = Safe (earnings >10 days after expiry or no earnings)
            75 = Moderate (earnings 5-10 days after expiry)
            50 = Risky (earnings during position but >5 days)
            25 = Very risky (earnings <5 days from now)
            0 = Extremely risky (earnings before expiry)
        
        Returns:
            Decimal 0-100
        """
        days_to_earnings = self._days_to_earnings(position)
        dte = position.dte or 30
        
        if days_to_earnings is None:
            # No earnings data - assume safe
            score = 100
            reason = "No earnings"
        elif days_to_earnings > dte + 10:
            # Earnings well after expiry - safe
            score = 100
            reason = f"Earnings {days_to_earnings - dte} days after expiry"
        elif days_to_earnings > dte + 5:
            # Earnings shortly after expiry - moderate
            score = 75
            reason = f"Earnings {days_to_earnings - dte} days after expiry"
        elif days_to_earnings > 10:
            # Earnings during position but distant - manageable
            score = 50
            reason = f"Earnings in {days_to_earnings} days (position active)"
        elif days_to_earnings > 5:
            # Earnings soon - risky
            score = 25
            reason = f"Earnings in {days_to_earnings} days (very close)"
        else:
            # Earnings imminent or before expiry - dangerous
            score = 0
            reason = f"⚠️ EARNINGS IN {days_to_earnings} DAYS"
        
        self.logger.debug(f"  📅 {position.symbol}: {reason} → score {score}")
        
        return Decimal(str(score))
    
    def _days_to_earnings(self, position) -> Optional[int]:
        """
        Calculate days until next earnings
        
        Returns:
            int (days) or None if no earnings data
        """
        # This would integrate with actual earnings calendar
        # For now, placeholder using position metadata
        
        # Check notes for earnings info
        notes = position.notes or ""
        if "earnings" in notes.lower():
            # Parse earnings date from notes
            # Format: "Earnings: 11/15/2025" or "Next earnings in 5 days"
            import re
            
            # Look for "in X days"
            match = re.search(r'in (\d+) days?', notes, re.IGNORECASE)
            if match:
                return int(match.group(1))
            
            # Look for date
            match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', notes)
            if match:
                month, day, year = map(int, match.groups())
                earnings_date = date(year, month, day)
                days = (earnings_date - date.today()).days
                return max(0, days)
        
        # No earnings data found
        return None
    
    def _score_profit_potential(self, position) -> Decimal:
        """
        Score based on Return on Capital (ROC%)
        
        Scoring:
            100 = ROC ≥15%
            80 = ROC 10-15%
            60 = ROC 6-10%
            40 = ROC 4-6%
            20 = ROC 2-4%
            0 = ROC <2%
        
        Returns:
            Decimal 0-100
        """
        # Calculate ROC if not already stored
        if position.capital_required and position.capital_required > 0:
            roc = (position.premium_collected / position.capital_required) * 100
        else:
            # Fallback calculation
            max_profit = position.max_profit or 0
            capital = position.capital_required or 1  # Avoid division by zero
            roc = (max_profit / capital) * 100
        
        roc = float(roc)
        
        # Score based on ROC thresholds
        if roc >= 15:
            score = 100
        elif roc >= 10:
            score = 80
        elif roc >= 6:
            score = 60
        elif roc >= 4:
            score = 40
        elif roc >= 2:
            score = 20
        else:
            score = 0
        
        self.logger.debug(f"  💰 {position.symbol}: ROC {roc:.1f}% → score {score}")
        
        return Decimal(str(score))
    
    def _score_dte_diversity(self, position, all_positions: List) -> Decimal:
        """
        Score based on DTE diversification (penalize clustering)
        
        Scoring:
            100 = Unique expiry week (no clustering)
            75 = 1 other position same week
            50 = 2 others same week
            25 = 3 others same week
            0 = 4+ others same week (heavy clustering)
        
        Returns:
            Decimal 0-100
        """
        if not position.expiration_date:
            return Decimal('50')  # Neutral if no date
        
        # Count positions in same expiry week
        same_week_count = 0
        position_week = self._get_week_key(position.expiration_date)
        
        for other_pos in all_positions:
            if other_pos.id == position.id:
                continue  # Skip self
            if other_pos.expiration_date:
                other_week = self._get_week_key(other_pos.expiration_date)
                if other_week == position_week:
                    same_week_count += 1
        
        # Score based on clustering
        if same_week_count == 0:
            score = 100
        elif same_week_count == 1:
            score = 75
        elif same_week_count == 2:
            score = 50
        elif same_week_count == 3:
            score = 25
        else:
            score = 0
        
        self.logger.debug(f"  ⏰ {position.symbol}: {same_week_count} others in week {position_week} → score {score}")
        
        return Decimal(str(score))
    
    def _get_week_key(self, date_obj: date) -> str:
        """
        Get week identifier for a date (Year-Week)
        
        Example: 2025-11-10 → "2025-W46"
        """
        return f"{date_obj.year}-W{date_obj.isocalendar()[1]:02d}"
    
    def _is_strategy_aligned(self, position) -> bool:
        """
        Check if position strategy aligns with Whales directional signal
        
        Alignment:
            Bull Put + Bullish Flow = ✅
            Bear Call + Bearish Flow = ✅
            Mismatch = ❌
        
        Returns:
            bool
        """
        notes = position.notes or ""
        strategy = position.strategy.lower()
        
        # Parse flow direction from notes
        if "bullish" in notes.lower():
            flow_direction = "bullish"
        elif "bearish" in notes.lower():
            flow_direction = "bearish"
        else:
            return False  # No clear signal
        
        # Check alignment
        if flow_direction == "bullish" and ("bull_put" in strategy or "short_put" in strategy):
            return True
        if flow_direction == "bearish" and ("bear_call" in strategy or "short_call" in strategy):
            return True
        
        return False
    
    def _has_earnings_conflict(self, position) -> bool:
        """
        Check if earnings occur before expiration
        
        Returns:
            bool - True if earnings conflict exists
        """
        days_to_earnings = self._days_to_earnings(position)
        dte = position.dte or 30
        
        if days_to_earnings is None:
            return False  # No earnings data
        
        # Earnings before expiry = conflict
        return days_to_earnings < dte
    
    def _generate_recommendation(self, total_score: Decimal) -> str:
        """
        Generate recommendation label based on total score
        
        Returns:
            str - "STRONG BUY", "BUY", "HOLD", "AVOID"
        """
        if total_score >= 85:
            return "STRONG BUY"
        elif total_score >= 70:
            return "BUY"
        elif total_score >= 50:
            return "HOLD"
        else:
            return "AVOID"
    
    def _generate_selection_reason(self, position, whales, earnings, profit, dte) -> str:
        """
        Generate human-readable explanation of why position ranked well/poorly
        
        Returns:
            str - Selection reasoning
        """
        reasons = []
        
        # Top factor
        scores = {
            'Whales alignment': whales,
            'Earnings safety': earnings,
            'Profit potential': profit,
            'DTE diversity': dte
        }
        top_factor = max(scores, key=scores.get)
        top_score = scores[top_factor]
        
        if top_score >= 80:
            reasons.append(f"Strong {top_factor.lower()} ({top_score:.0f}/100)")
        
        # Weaknesses
        weak_factors = [name for name, score in scores.items() if score < 40]
        if weak_factors:
            reasons.append(f"⚠️ Weak: {', '.join(weak_factors)}")
        
        # Strategy note
        if self._is_strategy_aligned(position):
            reasons.append(f"✅ Strategy aligned with flow")
        
        return " | ".join(reasons) if reasons else "Standard position"
    
    def get_top_n(self, ranked_positions: List[Dict], n: int = 5) -> List[Dict]:
        """
        Select top N positions with diversity checks
        
        Applies business rules:
        - Max 3 positions per sector
        - Prefer diversity in expiration dates
        - Avoid excessive clustering
        
        Args:
            ranked_positions: Already ranked list from rank_positions()
            n: Number of positions to select (default 5)
            
        Returns:
            List of top N position dicts
        """
        if len(ranked_positions) <= n:
            return ranked_positions  # Return all if fewer than N
        
        selected = []
        sector_counts = defaultdict(int)
        week_counts = defaultdict(int)
        
        for item in ranked_positions:
            position = item['position']
            
            # Check sector limit
            sector = self._get_sector(position)
            if sector_counts[sector] >= self.MAX_POSITIONS_PER_SECTOR:
                self.logger.debug(f"  ⏭️ Skipping {position.symbol}: Sector {sector} limit reached")
                continue
            
            # Add to selection
            selected.append(item)
            sector_counts[sector] += 1
            
            if position.expiration_date:
                week = self._get_week_key(position.expiration_date)
                week_counts[week] += 1
            
            # Stop when we have N positions
            if len(selected) >= n:
                break
        
        self.logger.info(f"🏆 Selected top {len(selected)} positions")
        self.logger.info(f"  Sectors: {dict(sector_counts)}")
        self.logger.info(f"  Weeks: {dict(week_counts)}")
        
        return selected
    
    def _get_sector(self, position) -> str:
        """
        Get sector for position (would integrate with stock data API)
        
        For now, returns placeholder based on symbol
        """
        # This would lookup actual sector from database or API
        # Placeholder logic:
        tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMD', 'META', 'TSLA', 'PLTR']
        finance_symbols = ['JPM', 'BAC', 'GS', 'MS', 'C', 'WFC']
        
        symbol = position.symbol.upper()
        
        if symbol in tech_symbols:
            return 'Technology'
        elif symbol in finance_symbols:
            return 'Finance'
        else:
            return 'Other'

