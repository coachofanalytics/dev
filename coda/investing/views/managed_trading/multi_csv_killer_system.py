"""
KILLER SYSTEM: Multi-CSV Cross-Validation Upload
Upload Short Puts + Covered Calls + Credit Spreads for cross-validation scoring
"""

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from decimal import Decimal
from datetime import datetime, date, timedelta
import csv
import io
import json
import logging

from ...models import OptionPlayRawData, SuggestedPosition
from ...services.optionplay_converter import OptionPlayConverterService
from ...services.position_scoring_service import PositionScoringService

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _detect_file_type(headers, first_row):
    """
    Auto-detect if CSV is Short Puts, Covered Calls, or Credit Spreads
    
    Returns: 'short_put', 'covered_call', 'credit_spread', or 'unknown'
    """
    headers_lower = [h.lower().strip() for h in headers if h]
    
    # Credit Spreads have unique headers
    if 'strategy' in headers_lower and 'buy strike' in headers_lower:
        return 'credit_spread'
    
    # Both Short Puts and Covered Calls have similar headers
    # Check the title row or action
    if first_row:
        first_cell = str(first_row[0]).lower()
        if 'short put' in first_cell:
            return 'short_put'
        elif 'covered call' in first_cell:
            return 'covered_call'
    
    # Check if "Action" column says "Sell to Open" (both SP and CC)
    if 'action' in headers_lower:
        # Default to short_put if unsure (most common)
        return 'short_put'
    
    return 'unknown'


def _read_and_classify_csv(csv_file):
    """
    Read CSV file and return dict with:
    - file_type: 'short_put', 'covered_call', 'credit_spread'
    - data: list of row dicts
    - symbol_list: set of symbols
    """
    try:
        # Read file content
        content = csv_file.read().decode('utf-8')
        csv_file.seek(0)  # Reset for potential re-read
        
        lines = content.split('\n')
        
        # Detect file type from first few rows
        reader = csv.reader(lines)
        rows = list(reader)
        
        if len(rows) < 2:
            return None
        
        # Find header row (skip title rows)
        header_row = None
        data_start = 0
        for i, row in enumerate(rows[:5]):
            if any('symbol' in cell.lower() for cell in row):
                header_row = row
                data_start = i + 1
                break
        
        if not header_row:
            return None
        
        # Detect file type
        file_type = _detect_file_type(header_row, rows[0] if rows else None)
        
        # Parse data rows
        data = []
        symbols = set()
        
        for row in rows[data_start:]:
            if not row or not row[0].strip():
                continue
            
            row_dict = {}
            for i, header in enumerate(header_row):
                if i < len(row):
                    row_dict[header.strip()] = row[i].strip()
            
            if row_dict.get('Symbol'):
                symbol = row_dict['Symbol'].upper().strip()
                symbols.add(symbol)
                row_dict['Symbol'] = symbol
                data.append(row_dict)
        
        return {
            'file_type': file_type,
            'filename': csv_file.name,
            'data': data,
            'symbols': symbols,
            'headers': header_row
        }
        
    except Exception as e:
        logger.error(f"Error reading CSV {csv_file.name}: {str(e)}")
        return None


def _calculate_cross_validation_score(symbol, sp_data, cc_data, cs_data):
    """
    Calculate conviction score for a symbol based on multiple data sources
    
    Scoring:
    +100: In all 3 strategies
    +50: In 2 strategies (SP + CC)
    +0: In 1 strategy only
    
    +30: IV Rank >50%
    +20: IV Rank 30-50%
    +10: IV Rank <30%
    
    +25: No earnings within 14 days
    -20: Earnings within 7 days
    
    +15: ROC >50%
    +10: ROC 30-50%
    +5: ROC <30%
    
    Returns: dict with score and breakdown
    """
    score = 0
    breakdown = {}
    
    # Strategy count (cross-validation)
    strategies = []
    if sp_data:
        strategies.append('Short Put')
    if cc_data:
        strategies.append('Covered Call')
    if cs_data:
        strategies.append('Credit Spread')
    
    strategy_count = len(strategies)
    if strategy_count == 3:
        score += 100
        breakdown['strategy'] = '+100 (All 3 strategies!)'
    elif strategy_count == 2:
        score += 50
        breakdown['strategy'] = '+50 (2 strategies - high conviction)'
    else:
        breakdown['strategy'] = '+0 (1 strategy only)'
    
    # IV Rank (use SP data as primary)
    iv_rank = None
    if sp_data:
        iv_str = sp_data.get('Implied Volatility Rank', '0').replace('%', '').strip()
        try:
            iv_rank = float(iv_str)
        except:
            iv_rank = 0
    
    if iv_rank:
        if iv_rank > 50:
            score += 30
            breakdown['iv_rank'] = f'+30 (IV {iv_rank}% - excellent)'
        elif iv_rank > 30:
            score += 20
            breakdown['iv_rank'] = f'+20 (IV {iv_rank}% - good)'
        else:
            score += 10
            breakdown['iv_rank'] = f'+10 (IV {iv_rank}% - moderate)'
    
    # Earnings risk
    earnings_flag = sp_data.get('Earnings Flag', 'N') if sp_data else 'N'
    earnings_date_str = sp_data.get('Earnings Date', '') if sp_data else ''
    
    if earnings_flag == 'Y' and earnings_date_str:
        # Parse earnings date
        try:
            earnings_date = datetime.strptime(earnings_date_str.split()[0], '%m/%d/%Y').date()
            days_to_earnings = (earnings_date - date.today()).days
            
            if days_to_earnings <= 7:
                score -= 20
                breakdown['earnings'] = f'-20 (Earnings in {days_to_earnings} days - risky!)'
            else:
                score += 25
                breakdown['earnings'] = f'+25 (Earnings in {days_to_earnings} days - safe window)'
        except:
            score += 10
            breakdown['earnings'] = '+10 (Earnings date unclear)'
    else:
        score += 25
        breakdown['earnings'] = '+25 (No immediate earnings)'
    
    # ROC (Return on Capital) - calculate from raw return
    roc = None
    if sp_data:
        return_str = sp_data.get('Raw Return', '0').replace('%', '').strip()
        try:
            roc = float(return_str)
        except:
            roc = 0
    
    if roc:
        if roc > 8:  # >8% return
            score += 15
            breakdown['roc'] = f'+15 (ROC {roc}% - excellent)'
        elif roc > 5:  # 5-8% return
            score += 10
            breakdown['roc'] = f'+10 (ROC {roc}% - good)'
        else:
            score += 5
            breakdown['roc'] = f'+5 (ROC {roc}% - moderate)'
    
    return {
        'score': score,
        'breakdown': breakdown,
        'strategies': strategies,
        'strategy_count': strategy_count,
        'iv_rank': iv_rank,
        'roc': roc,
        'earnings_flag': earnings_flag,
        'earnings_date': earnings_date_str
    }


@staff_member_required
def killer_system_upload(request):
    """
    KILLER SYSTEM: Multi-CSV Upload Step 1
    Upload Short Puts, Covered Calls, and/or Credit Spreads
    """
    logger.info("=" * 80)
    logger.info("🎯 KILLER SYSTEM: MULTI-CSV UPLOAD - STEP 1")
    logger.info("=" * 80)
    
    if request.method == 'POST':
        # Get uploaded files
        sp_file = request.FILES.get('short_puts_file')
        cc_file = request.FILES.get('covered_calls_file')
        cs_file = request.FILES.get('credit_spreads_file')
        
        if not sp_file and not cc_file and not cs_file:
            messages.error(request, 'Please upload at least one CSV file')
            return render(request, 'investing/managed/killer_system_step1.html')
        
        logger.info(f"📥 Files received:")
        if sp_file:
            logger.info(f"   ✅ Short Puts: {sp_file.name}")
        if cc_file:
            logger.info(f"   ✅ Covered Calls: {cc_file.name}")
        if cs_file:
            logger.info(f"   ✅ Credit Spreads: {cs_file.name}")
        
        try:
            # Read and classify all files
            sp_parsed = _read_and_classify_csv(sp_file) if sp_file else None
            cc_parsed = _read_and_classify_csv(cc_file) if cc_file else None
            cs_parsed = _read_and_classify_csv(cs_file) if cs_file else None
            
            if not any([sp_parsed, cc_parsed, cs_parsed]):
                messages.error(request, 'Error parsing CSV files. Please check file format.')
                return render(request, 'investing/managed/killer_system_step1.html')
            
            # Collect all symbols
            all_symbols = set()
            if sp_parsed:
                all_symbols.update(sp_parsed['symbols'])
            if cc_parsed:
                all_symbols.update(cc_parsed['symbols'])
            if cs_parsed:
                all_symbols.update(cs_parsed['symbols'])
            
            logger.info(f"📊 Total unique symbols: {len(all_symbols)}")
            
            # Find overlaps
            sp_symbols = sp_parsed['symbols'] if sp_parsed else set()
            cc_symbols = cc_parsed['symbols'] if cc_parsed else set()
            cs_symbols = cs_parsed['symbols'] if cs_parsed else set()
            
            sp_cc_overlap = sp_symbols.intersection(cc_symbols)
            sp_cs_overlap = sp_symbols.intersection(cs_symbols)
            all_three_overlap = sp_symbols.intersection(cc_symbols, cs_symbols)
            
            logger.info(f"💎 SP + CC overlap: {len(sp_cc_overlap)} symbols (HIGH CONVICTION!)")
            logger.info(f"💎 SP + CS overlap: {len(sp_cs_overlap)} symbols")
            logger.info(f"🏆 All 3 strategies: {len(all_three_overlap)} symbols (ULTRA HIGH!)")
            
            # Create lookup dicts
            sp_dict = {row['Symbol']: row for row in sp_parsed['data']} if sp_parsed else {}
            cc_dict = {row['Symbol']: row for row in cc_parsed['data']} if cc_parsed else {}
            cs_dict = {row['Symbol']: row for row in cs_parsed['data']} if cs_parsed else {}
            
            # Calculate scores for all symbols
            scored_symbols = []
            for symbol in all_symbols:
                sp_data = sp_dict.get(symbol)
                cc_data = cc_dict.get(symbol)
                cs_data = cs_dict.get(symbol)
                
                score_result = _calculate_cross_validation_score(symbol, sp_data, cc_data, cs_data)
                
                scored_symbols.append({
                    'symbol': symbol,
                    'score': score_result['score'],
                    'breakdown': score_result['breakdown'],
                    'strategies': score_result['strategies'],
                    'strategy_count': score_result['strategy_count'],
                    'iv_rank': score_result['iv_rank'],
                    'roc': score_result['roc'],
                    'earnings_flag': score_result['earnings_flag'],
                    'sp_data': sp_data,
                    'cc_data': cc_data,
                    'cs_data': cs_data,
                })
            
            # Sort by score
            scored_symbols.sort(key=lambda x: x['score'], reverse=True)
            
            # Store in session
            request.session['killer_system_data'] = {
                'scored_symbols': json.dumps(scored_symbols, default=str),
                'sp_filename': sp_file.name if sp_file else None,
                'cc_filename': cc_file.name if cc_file else None,
                'cs_filename': cs_file.name if cs_file else None,
                'total_symbols': len(all_symbols),
                'sp_cc_overlap': len(sp_cc_overlap),
                'all_three_overlap': len(all_three_overlap),
            }
            
            logger.info("✅ Cross-validation analysis complete!")
            return redirect('investing:killer_system_filter')
            
        except Exception as e:
            logger.error(f"❌ Error processing files: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing files: {str(e)}')
            return render(request, 'investing/managed/killer_system_step1.html')
    
    # GET request - show upload form
    context = {
        'title': 'KILLER SYSTEM: Multi-CSV Upload'
    }
    return render(request, 'investing/managed/killer_system_step1.html', context)


@staff_member_required
def killer_system_filter(request):
    """
    KILLER SYSTEM: Step 2 - Filter and Rank Results
    """
    logger.info("=" * 80)
    logger.info("🎯 KILLER SYSTEM: FILTER & RANK - STEP 2")
    logger.info("=" * 80)
    
    # Get data from session
    killer_data = request.session.get('killer_system_data')
    if not killer_data:
        messages.error(request, 'Session expired. Please upload files again.')
        return redirect('investing:killer_system_upload')
    
    scored_symbols = json.loads(killer_data['scored_symbols'])
    
    # Apply filters if POST
    if request.method == 'POST':
        min_score = int(request.POST.get('min_score', 50))
        min_strategies = int(request.POST.get('min_strategies', 1))
        exclude_earnings = request.POST.get('exclude_earnings') == 'on'
        min_iv = float(request.POST.get('min_iv', 0))
        
        # Filter
        filtered_symbols = []
        for item in scored_symbols:
            if item['score'] < min_score:
                continue
            if item['strategy_count'] < min_strategies:
                continue
            if exclude_earnings and item['earnings_flag'] == 'Y':
                continue
            if item['iv_rank'] and item['iv_rank'] < min_iv:
                continue
            
            filtered_symbols.append(item)
        
        logger.info(f"📊 Filtered: {len(scored_symbols)} → {len(filtered_symbols)} symbols")
    else:
        filtered_symbols = scored_symbols
    
    context = {
        'title': 'KILLER SYSTEM: Filter & Rank',
        'scored_symbols': filtered_symbols[:50],  # Top 50
        'total_symbols': len(scored_symbols),
        'filtered_count': len(filtered_symbols),
        'sp_filename': killer_data.get('sp_filename'),
        'cc_filename': killer_data.get('cc_filename'),
        'cs_filename': killer_data.get('cs_filename'),
        'sp_cc_overlap': killer_data.get('sp_cc_overlap'),
        'all_three_overlap': killer_data.get('all_three_overlap'),
    }
    
    return render(request, 'investing/managed/killer_system_step2.html', context)

