"""
Multi-File Flow Analyzer (Manual Unusual Whales Download Workflow)

Handles simultaneous upload of:
- 3 OptionPlay CSVs (Short Puts, Covered Calls, Credit Spreads)
- 4 Unusual Whales CSVs (Options Flow, Dark Pool, Lit Flow, Unusual Activity)

Generates entry signals (🟢🟡🔴) based on cross-validation + flow confirmation.
"""

import csv
import io
import json
import logging
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone

logger = logging.getLogger(__name__)


@staff_member_required
def multi_file_flow_analyzer(request):
    """
    Step 1: Upload all files at once (OptionPlay + Unusual Whales)
    
    Accepts:
    - optionplay_shortputs (optional)
    - optionplay_coveredcalls (optional)
    - optionplay_creditspreads (optional)
    - whales_options_flow (optional)
    - whales_dark_pool (optional)
    - whales_lit_flow (optional)
    - whales_unusual_activity (optional)
    
    Minimum: 1 OptionPlay file required
    """
    logger.info("=" * 80)
    logger.info("🐋 MULTI-FILE FLOW ANALYZER")
    logger.info("=" * 80)
    
    if request.method == 'POST':
        try:
            # Collect all uploaded files
            files_uploaded = {
                'optionplay_shortputs': request.FILES.get('optionplay_shortputs'),
                'optionplay_coveredcalls': request.FILES.get('optionplay_coveredcalls'),
                'optionplay_creditspreads': request.FILES.get('optionplay_creditspreads'),
                'whales_options_flow': request.FILES.get('whales_options_flow'),
                'whales_dark_pool': request.FILES.get('whales_dark_pool'),
                'whales_lit_flow': request.FILES.get('whales_lit_flow'),
                'whales_unusual_activity': request.FILES.get('whales_unusual_activity'),
            }
            
            # Count files
            file_count = sum(1 for f in files_uploaded.values() if f)
            logger.info(f"📥 Received {file_count} files for analysis")
            
            # Require at least 1 OptionPlay file
            optionplay_count = sum(1 for k, f in files_uploaded.items() if f and k.startswith('optionplay'))
            if optionplay_count == 0:
                messages.error(request, 'At least 1 OptionPlay file required')
                return render(request, 'investing/managed/multi_file_analyzer_step1.html')
            
            logger.info(f"✅ OptionPlay files: {optionplay_count}")
            logger.info(f"✅ Unusual Whales files: {file_count - optionplay_count}")
            
            # Parse all files
            logger.info("📊 Parsing files...")
            parsed_data = {}
            
            for file_type, file in files_uploaded.items():
                if file:
                    logger.info(f"  📄 Parsing {file_type}: {file.name}")
                    parsed_data[file_type] = _parse_csv_file(file)
                    logger.info(f"     ✅ {len(parsed_data[file_type])} rows")
            
            # Extract symbols from all files
            logger.info("🔍 Extracting symbols from all files...")
            symbols_by_file = {}
            
            for file_type, rows in parsed_data.items():
                symbols = _extract_symbols_from_rows(rows, file_type)
                symbols_by_file[file_type] = symbols
                logger.info(f"  {file_type}: {len(symbols)} unique symbols")
            
            # Cross-reference and score
            logger.info("🎯 Cross-referencing symbols and calculating conviction scores...")
            scored_symbols = _calculate_conviction_scores(parsed_data, symbols_by_file)
            
            logger.info(f"✅ Scored {len(scored_symbols)} unique symbols")
            
            # Store in session
            request.session['scored_symbols'] = json.dumps(scored_symbols, default=str)
            request.session['file_count'] = file_count
            request.session['optionplay_count'] = optionplay_count
            
            logger.info("✅ Redirecting to results page...")
            return redirect('investing:multi_file_analyzer_results')
        
        except Exception as e:
            logger.error(f"❌ Error processing files: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing files: {str(e)}')
            return render(request, 'investing/managed/multi_file_analyzer_step1.html')
    
    # GET request - show upload form
    context = {
        'title': 'Multi-File Flow Analyzer - Upload'
    }
    return render(request, 'investing/managed/multi_file_analyzer_step1.html', context)


@staff_member_required
def multi_file_analyzer_results(request):
    """
    Step 2: Show analyzed results with entry signals
    """
    scored_symbols_json = request.session.get('scored_symbols')
    if not scored_symbols_json:
        messages.error(request, 'No data found. Please upload files first.')
        return redirect('investing:multi_file_analyzer')
    
    scored_symbols = json.loads(scored_symbols_json)
    file_count = request.session.get('file_count', 0)
    optionplay_count = request.session.get('optionplay_count', 0)
    
    # Sort by total score (highest first)
    scored_symbols.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Categorize by signal
    green_signals = [s for s in scored_symbols if s['signal'] == 'green']
    yellow_signals = [s for s in scored_symbols if s['signal'] == 'yellow']
    red_signals = [s for s in scored_symbols if s['signal'] == 'red']
    
    context = {
        'scored_symbols': scored_symbols,
        'green_signals': green_signals,
        'yellow_signals': yellow_signals,
        'red_signals': red_signals,
        'file_count': file_count,
        'optionplay_count': optionplay_count,
        'title': 'Multi-File Flow Analyzer - Results'
    }
    
    return render(request, 'investing/managed/multi_file_analyzer_results.html', context)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _parse_csv_file(file):
    """Parse uploaded CSV file and return list of dictionaries"""
    try:
        file_data = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(file_data))
        return list(csv_reader)
    except Exception as e:
        logger.error(f"Error parsing {file.name}: {str(e)}")
        return []


def _extract_symbols_from_rows(rows, file_type):
    """Extract unique symbols from parsed CSV rows"""
    symbols = set()
    
    # Different files have different column names for symbols
    symbol_columns = ['symbol', 'ticker', 'Symbol', 'Ticker', 'underlying']
    
    for row in rows:
        for col in symbol_columns:
            if col in row and row[col]:
                symbol = row[col].strip().upper()
                if symbol and len(symbol) <= 10:
                    symbols.add(symbol)
                break
    
    return list(symbols)


def _calculate_conviction_scores(parsed_data, symbols_by_file):
    """
    Calculate conviction score for each symbol based on appearances across files
    
    Scoring:
    - OptionPlay file: +30 pts each (max 90 for all 3)
    - Dark Pool buying: +20 pts
    - Options Flow bullish: +20 pts
    - Unusual Activity: +15 pts
    - Cross-validated (2+ OptionPlay): +50 pts
    
    Signals:
    - 80-100: 🟢 GREEN (ENTER NOW!)
    - 50-79: 🟡 YELLOW (OK to enter)
    - 0-49: 🔴 RED (SKIP/WAIT)
    """
    # Get all unique symbols
    all_symbols = set()
    for symbols in symbols_by_file.values():
        all_symbols.update(symbols)
    
    scored_symbols = []
    
    for symbol in all_symbols:
        score = 0
        details = {
            'symbol': symbol,
            'optionplay_appearances': 0,
            'optionplay_files': [],
            'dark_pool_detected': False,
            'options_flow_detected': False,
            'unusual_activity_detected': False,
            'lit_flow_detected': False,
            'details': []
        }
        
        # Check OptionPlay files
        for file_type, symbols_list in symbols_by_file.items():
            if file_type.startswith('optionplay') and symbol in symbols_list:
                details['optionplay_appearances'] += 1
                details['optionplay_files'].append(file_type.replace('optionplay_', ''))
                score += 30
        
        # Cross-validation bonus (appears in 2+ OptionPlay files)
        if details['optionplay_appearances'] >= 2:
            score += 50
            details['details'].append('💎 Cross-Validated (appears in multiple OptionPlay lists)')
        
        # Check Unusual Whales files
        if 'whales_dark_pool' in symbols_by_file and symbol in symbols_by_file['whales_dark_pool']:
            details['dark_pool_detected'] = True
            score += 20
            details['details'].append('🟢 Dark Pool activity detected (institutional interest)')
        
        if 'whales_options_flow' in symbols_by_file and symbol in symbols_by_file['whales_options_flow']:
            details['options_flow_detected'] = True
            score += 20
            details['details'].append('🟢 Options flow detected (smart money active)')
        
        if 'whales_unusual_activity' in symbols_by_file and symbol in symbols_by_file['whales_unusual_activity']:
            details['unusual_activity_detected'] = True
            score += 15
            details['details'].append('⚡ Unusual activity (abnormal volume)')
        
        if 'whales_lit_flow' in symbols_by_file and symbol in symbols_by_file['whales_lit_flow']:
            details['lit_flow_detected'] = True
            score += 5
            details['details'].append('📊 Lit flow detected (market interest)')
        
        # Determine signal
        if score >= 80:
            signal = 'green'
            signal_text = '🟢 ENTER NOW'
            recommendation = 'High conviction - Multiple confirmations across OptionPlay + Flow data'
        elif score >= 50:
            signal = 'yellow'
            signal_text = '🟡 OK TO ENTER'
            recommendation = 'Moderate conviction - OptionPlay screened, some flow confirmation'
        else:
            signal = 'red'
            signal_text = '🔴 SKIP/WAIT'
            recommendation = 'Low conviction - Limited confirmations or missing flow data'
        
        details['total_score'] = score
        details['signal'] = signal
        details['signal_text'] = signal_text
        details['recommendation'] = recommendation
        
        scored_symbols.append(details)
    
    return scored_symbols

