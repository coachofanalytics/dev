"""
CSV Upload Wizard for OptionPlay Data

Multi-step wizard with preview, field mapping, quality filters, and AI scoring.
"""

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from decimal import Decimal
from datetime import datetime, date
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


@staff_member_required
def csv_upload_wizard(request):
    """
    Step 1: Upload CSV file and show preview
    
    GET: Show upload form
    POST: Accept CSV, show preview
    """
    logger.info("=" * 80)
    logger.info("🚀 CSV UPLOAD WIZARD - STEP 1")
    logger.info("=" * 80)
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        logger.info(f"📥 File received: {csv_file.name}")
        logger.info(f"📊 File size: {csv_file.size / 1024:.2f} KB ({csv_file.size} bytes)")
        logger.info(f"📁 Content type: {csv_file.content_type}")
        
        # Validate file type
        file_extension = csv_file.name.lower().split('.')[-1]
        valid_extensions = ['csv', 'xlsx', 'xls']
        
        if file_extension not in valid_extensions:
            logger.error(f"❌ Invalid file type: {csv_file.name}")
            messages.error(request, 'Please upload a CSV (.csv) or Excel (.xlsx, .xls) file')
            return render(request, 'investing/managed/csv_upload_step1.html')
        
        logger.info(f"✅ File type validated: {file_extension.upper()}")
        
        try:
            # Determine how to read the file based on extension
            if file_extension in ['xlsx', 'xls']:
                logger.info("📖 Reading Excel file...")
                file_data = _read_excel_to_csv_string(csv_file, file_extension)
                logger.info(f"✅ Excel converted to CSV format ({len(file_data)} characters)")
            else:
                logger.info("📖 Reading CSV file...")
                file_data = csv_file.read().decode('utf-8')
                logger.info(f"✅ File decoded successfully ({len(file_data)} characters)")
            
            # Smart header detection - skip title rows
            logger.info("🔍 Detecting header row (skipping title rows if present)...")
            lines = file_data.split('\n')
            header_row_index = 0
            
            # Look for the row with actual column headers
            for i, line in enumerate(lines[:10]):  # Check first 10 rows
                if not line.strip():
                    continue
                    
                # Split line to check for known column names
                fields = [f.strip().strip('"').strip("'") for f in line.split(',')]
                non_empty = [f for f in fields if f]
                
                logger.debug(f"  Row {i}: {len(non_empty)} non-empty fields, Sample: {non_empty[:3]}")
                
                # Check if this row contains expected header keywords
                headers_found = sum(1 for f in fields if any(keyword in f.lower() for keyword in 
                    ['symbol', 'strike', 'expiry', 'premium', 'price', 'action', 'dte', 'days']))
                
                if headers_found >= 3:  # Found at least 3 expected headers
                    header_row_index = i
                    logger.info(f"✅ Header row detected at line {i + 1} (found {headers_found} known headers)")
                    logger.info(f"   Headers preview: {', '.join(non_empty[:5])}")
                    break
            
            # Skip rows before the header
            if header_row_index > 0:
                logger.info(f"⏭️  Skipping {header_row_index} title/empty rows before header")
                file_data = '\n'.join(lines[header_row_index:])
            
            csv_reader = csv.DictReader(io.StringIO(file_data))
            
            # Get headers and preview data
            headers = csv_reader.fieldnames
            
            # Clean headers (remove empty or None headers)
            headers_cleaned = [h for h in headers if h and h.strip()]
            if len(headers_cleaned) < len(headers):
                logger.warning(f"⚠️  Removed {len(headers) - len(headers_cleaned)} empty headers")
                # Recreate reader with cleaned data
                cleaned_lines = [','.join(headers_cleaned)]
                for row in csv_reader:
                    values = [row.get(h, '') for h in headers_cleaned]
                    cleaned_lines.append(','.join(values))
                file_data = '\n'.join(cleaned_lines)
                csv_reader = csv.DictReader(io.StringIO(file_data))
                headers = headers_cleaned
            
            logger.info(f"📋 CSV Headers detected: {headers}")
            logger.info(f"📊 Number of columns: {len(headers)}")
            
            preview_rows = []
            all_rows = []
            
            logger.info("📊 Processing CSV rows...")
            for i, row in enumerate(csv_reader):
                all_rows.append(row)
                if i < 5:  # Preview first 5 rows
                    preview_rows.append(row)
                
                # Log progress every 100 rows
                if (i + 1) % 100 == 0:
                    logger.debug(f"  ... processed {i + 1} rows")
            
            total_rows = len(all_rows)
            logger.info(f"✅ CSV processing complete: {total_rows} rows read")
            logger.info(f"📋 Preview rows: {len(preview_rows)}")
            
            # Store CSV data in session for next step
            logger.info("💾 Storing data in session...")
            request.session['csv_data'] = json.dumps(all_rows)
            request.session['csv_headers'] = headers
            request.session['csv_filename'] = csv_file.name
            
            # Auto-map columns intelligently
            logger.info("🤖 Auto-mapping columns to database fields...")
            field_mapping = _auto_map_columns(headers)
            
            # Store mapping in session
            request.session['field_mapping'] = field_mapping
            
            # Detect strategy type from filename or first row
            logger.info("🔍 Detecting strategy type...")
            strategy_type = _detect_strategy_type(csv_file.name, headers)
            request.session['strategy_type'] = strategy_type
            logger.info(f"✅ Strategy detected: {strategy_type}")
            
            # Calculate statistics for filter suggestions
            logger.info("📊 Calculating CSV statistics...")
            stats = _calculate_csv_stats(all_rows, field_mapping)
            
            # Get existing data counts for cleanup context (BOTH tables!)
            from django.utils import timezone
            from datetime import timedelta
            
            # OptionPlayRawData counts
            existing_raw_total = OptionPlayRawData.objects.count()
            existing_raw_expired = OptionPlayRawData.objects.filter(expiry__lt=timezone.now().date()).count()
            existing_raw_active = existing_raw_total - existing_raw_expired
            
            # SuggestedPositions counts
            existing_suggested_total = SuggestedPosition.objects.count()
            cutoff_date = timezone.now() - timedelta(days=7)  # 7 days (suggestions go stale fast!)
            existing_suggested_old = SuggestedPosition.objects.filter(
                Q(expiration_date__lt=timezone.now().date()) |  # Expired
                Q(fetched_at__lt=cutoff_date)  # Older than 7 days
            ).count()
            existing_suggested_active = existing_suggested_total - existing_suggested_old
            
            logger.info(f"📊 Existing OptionPlayRawData: {existing_raw_total} total ({existing_raw_active} active, {existing_raw_expired} expired)")
            logger.info(f"📊 Existing SuggestedPositions: {existing_suggested_total} total ({existing_suggested_active} active, {existing_suggested_old} old/expired >7 days)")
            
            logger.info("=" * 80)
            logger.info("📊 UPLOAD SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Filename: {csv_file.name}")
            logger.info(f"Size: {csv_file.size / 1024:.2f} KB")
            logger.info(f"Rows: {total_rows}")
            logger.info(f"Columns: {len(headers)}")
            logger.info(f"Mapped: {len([v for v in field_mapping.values() if v != 'skip'])}")
            logger.info(f"Skipped: {len([v for v in field_mapping.values() if v == 'skip'])}")
            logger.info(f"Strategy: {strategy_type}")
            logger.info("=" * 80)
            
            # Calculate percentage display values for template
            stats_with_percentages = {
                'avg_premium': stats['avg_premium'],
                'avg_iv': stats['avg_iv'],
                'avg_iv_pct': float(stats['avg_iv'] * 100),  # 0.28 → 28% for display
                'avg_dte': stats['avg_dte'],
                'unique_symbols': stats['unique_symbols'],
                'symbols_list': stats['symbols_list'],
            }
            
            context = {
                'headers': headers,
                'preview_rows': preview_rows[:5],  # First 5 for preview
                'total_rows': len(all_rows),
                'filename': csv_file.name,
                'strategy_type': strategy_type,
                'title': 'CSV Upload - Step 2: Confirm & Filter',
                'skipped_rows': header_row_index,
                'field_mapping': field_mapping,
                'stats': stats_with_percentages,
                # OptionPlayRawData counts
                'existing_raw_total': existing_raw_total,
                'existing_raw_active': existing_raw_active,
                'existing_raw_expired': existing_raw_expired,
                # SuggestedPositions counts
                'existing_suggested_total': existing_suggested_total,
                'existing_suggested_active': existing_suggested_active,
                'existing_suggested_old': existing_suggested_old,
            }
            
            logger.info("✅ Rendering Step 2 (Confirm & Filter) - Skipping manual mapping")
            return render(request, 'investing/managed/csv_upload_step2_auto.html', context)
            
        except ValueError as e:
            # User-friendly error for .xls or format issues
            logger.error(f"❌ Value error: {str(e)}")
            messages.error(request, str(e))
            return render(request, 'investing/managed/csv_upload_step1.html')
        except UnicodeDecodeError as e:
            logger.error(f"❌ Unicode decode error: {str(e)}")
            logger.error("💡 Tip: Try saving the file with UTF-8 encoding")
            messages.error(request, f'Error reading file (encoding issue): {str(e)}. Try saving with UTF-8 encoding.')
            return render(request, 'investing/managed/csv_upload_step1.html')
        except csv.Error as e:
            logger.error(f"❌ CSV parsing error: {str(e)}")
            messages.error(request, f'Error parsing CSV: {str(e)}')
            return render(request, 'investing/managed/csv_upload_step1.html')
        except ImportError as e:
            logger.error(f"❌ Import error (missing library): {str(e)}")
            if 'xlrd' in str(e).lower():
                messages.error(request, 'Legacy .xls format not supported. Please save your file as .xlsx in Excel and try again.')
            else:
                messages.error(request, f'Missing required library: {str(e)}')
            return render(request, 'investing/managed/csv_upload_step1.html')
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
            messages.error(request, f'Error reading file: {str(e)}')
            return render(request, 'investing/managed/csv_upload_step1.html')
    
    logger.info("📄 Rendering Step 1 (Upload Form)")
    context = {
        'title': 'CSV Upload - Step 1: Upload File'
    }
    return render(request, 'investing/managed/csv_upload_step1.html', context)


@staff_member_required
@require_http_methods(["POST"])
def csv_process_mapping(request):
    """
    Step 2: Process field mapping and show filter options
    
    POST: Receive field mapping, show quality filters
    """
    try:
        # Get CSV data from session
        csv_data = json.loads(request.session.get('csv_data', '[]'))
        headers = request.session.get('csv_headers', [])
        strategy_type = request.session.get('strategy_type', 'short_put')
        
        if not csv_data:
            messages.error(request, 'Session expired. Please upload CSV again.')
            return redirect('investing:csv_upload_wizard')
        
        # Get field mapping from form
        field_mapping = {}
        for csv_header in headers:
            model_field = request.POST.get(f'map_{csv_header}')
            if model_field and model_field != 'skip':
                field_mapping[csv_header] = model_field
        
        # Store mapping in session
        request.session['field_mapping'] = field_mapping
        
        # Calculate statistics for filter suggestions
        stats = _calculate_csv_stats(csv_data, field_mapping)
        
        context = {
            'total_rows': len(csv_data),
            'field_mapping': field_mapping,
            'stats': stats,
            'strategy_type': strategy_type,
            'title': 'CSV Upload - Step 3: Quality Filters'
        }
        
        return render(request, 'investing/managed/csv_upload_step3.html', context)
        
    except Exception as e:
        messages.error(request, f'Error processing mapping: {str(e)}')
        return redirect('investing:csv_upload_wizard')


@staff_member_required
@require_http_methods(["POST"])
def csv_import_and_score(request):
    """
    Step 3: Import with filters and AI scoring
    
    POST: Apply filters, import, convert, score
    """
    logger.info("=" * 80)
    logger.info("🚀 CSV UPLOAD WIZARD - STEP 3: IMPORT & SCORE")
    logger.info("=" * 80)
    
    try:
        # Get session data
        logger.info("📋 Retrieving session data...")
        csv_data = json.loads(request.session.get('csv_data', '[]'))
        field_mapping = request.session.get('field_mapping', {})
        strategy_type = request.session.get('strategy_type', 'short_put')
        
        logger.info(f"✅ CSV rows in session: {len(csv_data)}")
        logger.info(f"✅ Field mappings: {len(field_mapping)}")
        logger.info(f"✅ Strategy type: {strategy_type}")
        
        if not csv_data or not field_mapping:
            logger.error("❌ Session data missing")
            messages.error(request, 'Session expired. Please start over.')
            return redirect('investing:csv_upload_wizard')
        
        # Get Tier 1 filter parameters (Quality Filters)
        logger.info("🔧 Reading Tier 1 filter parameters (Quality)...")
        min_premium = Decimal(request.POST.get('min_premium', '0'))
        min_iv = Decimal(request.POST.get('min_iv', '0'))
        max_dte = int(request.POST.get('max_dte', '365'))
        max_positions = int(request.POST.get('max_positions', '100'))
        min_roc = Decimal(request.POST.get('min_roc', '0'))  # Minimum Return on Capital %
        spread_width_choice = request.POST.get('spread_width', 'auto')
        auto_convert = request.POST.get('auto_convert') == 'on'
        auto_score = request.POST.get('auto_score') == 'on'
        symbol_filter = request.POST.get('symbol_filter', '').strip()
        import_mode = request.POST.get('import_mode', 'add')  # add, replace, cleanup
        
        # Get Tier 2 filter parameters (Final Selection)
        tier2_enabled = request.POST.get('tier2_enabled') == 'on'
        exclude_earnings = request.POST.get('exclude_earnings') == 'on'
        blue_chip_only = request.POST.get('blue_chip_only') == 'on'
        min_stock_price = Decimal(request.POST.get('min_stock_price', '40'))
        max_stock_price = Decimal(request.POST.get('max_stock_price', '600'))
        min_distance_otm = Decimal(request.POST.get('min_distance_otm', '0.03'))  # 3% OTM
        tier2_ranking = request.POST.get('tier2_ranking', 'ai_score')  # ai_score, roc, balanced
        tier2_max_positions = int(request.POST.get('tier2_max_positions', '12'))
        
        logger.info("=" * 80)
        logger.info("📊 IMPORT SETTINGS (Two-Tier Filtering)")
        logger.info("=" * 80)
        logger.info(f"Import Mode: {import_mode.upper()}")
        logger.info("")
        logger.info("TIER 1 (Quality Filters):")
        logger.info(f"  Min Premium: ${min_premium}")
        logger.info(f"  Min IV Rank: {min_iv*100:.1f}% (Excel: {min_iv})")
        logger.info(f"  Max DTE: {max_dte} days")
        logger.info(f"  Min ROC: {min_roc*100:.1f}% (Excel: {min_roc})")
        logger.info(f"  Spread Width: {spread_width_choice}")
        logger.info(f"  Max Tier 1 Positions: {max_positions}")
        logger.info(f"  Symbol Filter: {symbol_filter or 'None (all symbols)'}")
        logger.info("")
        logger.info(f"TIER 2 (Final Selection): {'ENABLED' if tier2_enabled else 'DISABLED'}")
        if tier2_enabled:
            logger.info(f"  Exclude Earnings: {exclude_earnings}")
            logger.info(f"  Blue Chip Only: {blue_chip_only}")
            logger.info(f"  Stock Price Range: ${min_stock_price} - ${max_stock_price}")
            logger.info(f"  Min Distance OTM: {min_distance_otm*100:.0f}%")
            logger.info(f"  Ranking Method: {tier2_ranking.upper()}")
            logger.info(f"  Max Final Positions: {tier2_max_positions}")
        logger.info("")
        logger.info(f"Auto-Convert: {auto_convert}")
        logger.info(f"Auto-Score: {auto_score}")
        logger.info("=" * 80)
        
        # Parse symbol filter
        if symbol_filter:
            allowed_symbols = [s.strip().upper() for s in symbol_filter.split(',')]
            logger.info(f"✅ Allowed symbols: {allowed_symbols}")
        else:
            allowed_symbols = None
            logger.info("✅ All symbols allowed")
        
        # Handle data cleanup based on import mode (for BOTH tables!)
        deleted_raw_count = 0
        deleted_suggested_count = 0
        archived_count = 0
        
        if import_mode == 'replace':
            logger.info("🗑️  REPLACE MODE: Fresh market data - deleting stale suggestions...")
            logger.info("   ℹ️  NOTE: Client-approved positions (OptionsPosition) are NEVER deleted!")
            
            # Delete old OptionPlayRawData (just CSV import data)
            old_raw_count = OptionPlayRawData.objects.count()
            OptionPlayRawData.objects.all().delete()
            deleted_raw_count = old_raw_count
            logger.info(f"   ✅ Deleted {deleted_raw_count} old OptionPlayRawData (CSV import data)")
            
            # Delete old SuggestedPositions (stale AI suggestions - market has moved!)
            old_suggested_count = SuggestedPosition.objects.count()
            SuggestedPosition.objects.all().delete()
            deleted_suggested_count = old_suggested_count
            logger.info(f"   ✅ Deleted {deleted_suggested_count} old SuggestedPositions (stale suggestions)")
            
            logger.info(f"✅ Total deleted: {deleted_raw_count + deleted_suggested_count} positions (fresh start!)")
            
        elif import_mode == 'cleanup':
            logger.info("🧹 CLEANUP MODE: Archiving expired from BOTH tables...")
            from django.utils import timezone
            from datetime import timedelta
            from django.db.models import Q
            
            # Delete expired OptionPlayRawData
            expired_raw = OptionPlayRawData.objects.filter(expiry__lt=timezone.now().date())
            expired_raw_count = expired_raw.count()
            
            if expired_raw_count > 0:
                logger.info(f"   Found {expired_raw_count} expired OptionPlayRawData")
                expired_raw.delete()
                archived_count += expired_raw_count
            
            # Delete old/expired SuggestedPositions (older than 7 days or expired)
            # Market moves fast - suggestions go stale quickly!
            cutoff_date = timezone.now() - timedelta(days=7)
            old_suggested = SuggestedPosition.objects.filter(
                Q(expiration_date__lt=timezone.now().date()) |  # Expired
                Q(fetched_at__lt=cutoff_date)  # Older than 7 days
            )
            old_suggested_count = old_suggested.count()
            
            if old_suggested_count > 0:
                logger.info(f"   Found {old_suggested_count} old/expired SuggestedPositions (>7 days)")
                old_suggested.delete()
                archived_count += old_suggested_count
            
            if archived_count > 0:
                logger.info(f"✅ Archived {archived_count} total positions")
            else:
                logger.info("   No expired positions found")
        
        else:  # 'add' mode
            logger.info("➕ ADD MODE: Keeping existing data in BOTH tables, adding new positions")
        
        # Import with TWO-TIER filtering
        logger.info("📥 Starting import process (Two-Tier Filtering)...")
        tier1_passed = []  # Positions that pass quality filters
        tier1_filtered = 0
        tier2_filtered = 0
        error_count = 0
        
        # Tier 1 filter debugging
        tier1_reasons = {
            'premium': 0,
            'iv_rank': 0,
            'dte': 0,
            'roc': 0,
            'symbol': 0,
        }
        # Tier 2 filter debugging
        tier2_reasons = {
            'earnings': 0,
            'blue_chip': 0,
            'stock_price': 0,
            'distance_otm': 0,
        }
        rejected_samples = []  # Store first 5 rejected for debugging
        
        for idx, row_data in enumerate(csv_data, 1):
            try:
                # Map fields
                mapped_data = {}
                for csv_field, model_field in field_mapping.items():
                    value = row_data.get(csv_field, '').strip()
                    mapped_data[model_field] = value
                
                # Apply quality filters - convert to proper types
                premium_str = mapped_data.get('premium', '') or '0'
                iv_rank_str = mapped_data.get('iv_rank', '') or '0'
                dte_str = mapped_data.get('dte', '') or '365'
                symbol = mapped_data.get('symbol', '').upper().strip()
                
                # Clean and convert values using helper functions
                premium = _clean_decimal_value(premium_str)
                iv_rank_val = _clean_decimal_value(iv_rank_str)  # Keep Excel decimal format (0.28)
                dte = _clean_int_value(dte_str)
                
                # Calculate spread width and capital efficiency
                sell_strike_str = mapped_data.get('sell_strike', '') or '0'
                sell_strike = _clean_decimal_value(sell_strike_str)
                
                # Determine optimal spread width
                spread_width = _calculate_spread_width(sell_strike, spread_width_choice)
                
                # Calculate capital requirement for spread
                capital_required = spread_width * 100  # Spread capital = width × 100
                
                # Calculate Return on Capital (ROC in decimal format: 0.40 = 40%)
                # NOTE: Premium is per share, need to multiply by 100 for contract value
                premium_total = premium * 100  # $3.65/share × 100 = $365 contract
                if capital_required > 0:
                    roc = premium_total / capital_required  # $365 / $500 = 0.73 (73%)
                else:
                    roc = Decimal('0')
                
                # TIER 1: Quality filter checks with detailed tracking
                tier1_failed = False
                tier1_reason = []
                
                if premium < min_premium:
                    tier1_reasons['premium'] += 1
                    tier1_reason.append(f"Premium ${premium} < ${min_premium}")
                    tier1_failed = True
                
                if iv_rank_val < min_iv:
                    tier1_reasons['iv_rank'] += 1
                    tier1_reason.append(f"IV {iv_rank_val*100:.1f}% < {min_iv*100:.1f}%")
                    tier1_failed = True
                
                if dte > max_dte:
                    tier1_reasons['dte'] += 1
                    tier1_reason.append(f"DTE {dte} > {max_dte}")
                    tier1_failed = True
                
                # Filter by Return on Capital (capital efficiency!)
                if roc < min_roc:
                    tier1_reasons['roc'] += 1
                    tier1_reason.append(f"ROC {roc*100:.1f}% < {min_roc*100:.1f}% (${premium_total} premium on ${capital_required} capital)")
                    tier1_failed = True
                
                if allowed_symbols and symbol not in allowed_symbols:
                    tier1_reasons['symbol'] += 1
                    tier1_reason.append(f"Symbol {symbol} not allowed")
                    tier1_failed = True
                
                if len(tier1_passed) >= max_positions:
                    tier1_failed = True
                    tier1_reason.append(f"Max Tier 1 positions reached ({max_positions})")
                
                if tier1_failed:
                    tier1_filtered += 1
                    # Store first 5 rejections for debugging
                    if len(rejected_samples) < 5:
                        rejected_samples.append({
                            'symbol': symbol,
                            'premium': premium_total,
                            'iv_rank': iv_rank_val,
                            'dte': dte,
                            'roc': roc,
                            'capital': capital_required,
                            'spread_width': spread_width,
                            'reasons': tier1_reason
                        })
                    continue
                
                # Passed Tier 1! Store position data for Tier 2 evaluation
                stock_price_val = _clean_decimal_value(mapped_data.get('price', '0'))
                distance_val = _clean_decimal_value(mapped_data.get('distance_to_strike', '0'))
                earnings_flag_val = mapped_data.get('earnings_flag', 'N').strip().upper()
                
                position_data = {
                    'mapped_data': mapped_data,
                    'symbol': symbol,
                    'premium_total': premium_total,
                    'roc': roc,
                    'spread_width': spread_width,
                    'capital_required': capital_required,
                    'sell_strike': sell_strike,
                    'stock_price': stock_price_val,
                    'distance': distance_val,
                    'earnings_flag': earnings_flag_val,
                    'iv_rank': iv_rank_val,
                    'dte': dte,
                }
                
                tier1_passed.append(position_data)
                
                logger.debug(f"  ✅ Tier 1 PASS - Row {idx}: {symbol} (Premium: ${premium_total}, ROC: {roc*100:.1f}%, {spread_width}pt spread)")
                
                # Progress logging
                if idx % 10 == 0:
                    logger.info(f"  📊 Progress: {idx}/{len(csv_data)} rows processed, {len(tier1_passed)} passed Tier 1")
                
            except Exception as e:
                logger.error(f"  ❌ Row {idx}: Error importing - {str(e)}")
                error_count += 1
                continue
        
        logger.info("=" * 80)
        logger.info("📊 TIER 1 COMPLETE (Quality Filters)")
        logger.info("=" * 80)
        logger.info(f"✅ Passed Tier 1: {len(tier1_passed)} positions")
        logger.info(f"🔍 Filtered Tier 1: {tier1_filtered} positions")
        logger.info(f"❌ Errors: {error_count} positions")
        logger.info("=" * 80)
        
        # TIER 2: Apply final selection filters (if enabled)
        final_positions = []
        
        if tier2_enabled and tier1_passed:
            logger.info("")
            logger.info("=" * 80)
            logger.info("🎯 TIER 2: FINAL SELECTION (Blue Chip + AI Ranking)")
            logger.info("=" * 80)
            
            # Define blue chip symbol list
            BLUE_CHIP_SYMBOLS = [
                # Mega Tech (Mag 7)
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA',
                # Large Tech
                'NFLX', 'ORCL', 'INTU', 'QCOM', 'AMAT', 'AMD', 'MU', 'LRCX', 'SNPS', 'AVGO', 'CRM', 'ADBE',
                # Finance/Crypto
                'COIN', 'JPM', 'BAC', 'GS', 'MS', 'V', 'MA',
                # Consumer
                'DIS', 'ABNB', 'SPOT', 'BABA', 'TGT', 'ROST', 'TJX', 'NKE', 'SBUX',
                # Industrial/Materials
                'DE', 'CEG', 'AEM', 'NEM', 'GDX', 'GLD',
                # Semiconductor
                'ARM', 'MRVL', 'WDC', 'NTAP',
                # Healthcare
                'GILD', 'NVO', 'UNH', 'JNJ',
                # Luxury/Auto
                'RACE', 'AZO', 'F', 'GM',
                # Enterprise
                'CW', 'ACN', 'CSCO', 'ANET', 'NOW',
                # ETFs
                'IBIT', 'GDXJ',
                # Others
                'STZ', 'CF', 'GLW', 'ETN', 'TXRH', 'TTWO', 'FICO', 'ARGX', 'SE', 'APP', 'AFRM', 'ZM', 'WPM',
                'SMCI', 'IONQ', 'CRWV', 'TTD', 'CORZ', 'SOUN', 'HOOD', 'DELL', 'BIDU'
            ]
            
            # Apply Tier 2 hard filters
            tier2_candidates = []
            for pos in tier1_passed:
                tier2_failed = False
                tier2_reason = []
                
                # Filter: Exclude earnings
                if exclude_earnings and pos['earnings_flag'] == 'Y':
                    tier2_reasons['earnings'] += 1
                    tier2_reason.append("Has earnings in window")
                    tier2_failed = True
                
                # Filter: Blue chip only
                if blue_chip_only and pos['symbol'] not in BLUE_CHIP_SYMBOLS:
                    tier2_reasons['blue_chip'] += 1
                    tier2_reason.append("Not a blue chip symbol")
                    tier2_failed = True
                
                # Filter: Stock price range
                if not (min_stock_price <= pos['stock_price'] <= max_stock_price):
                    tier2_reasons['stock_price'] += 1
                    tier2_reason.append(f"Stock price ${pos['stock_price']} outside range")
                    tier2_failed = True
                
                # Filter: Minimum distance OTM (safety margin)
                # Distance is negative for OTM puts (-4% = 4% below stock)
                if pos['distance'] > -min_distance_otm:  # e.g., -0.02 > -0.03 means too close
                    tier2_reasons['distance_otm'] += 1
                    tier2_reason.append(f"Only {abs(pos['distance'])*100:.1f}% OTM (want ≥{min_distance_otm*100:.0f}%)")
                    tier2_failed = True
                
                if tier2_failed:
                    tier2_filtered += 1
                    logger.debug(f"  🔍 Tier 2 FILTERED: {pos['symbol']} - {', '.join(tier2_reason)}")
                else:
                    tier2_candidates.append(pos)
                    logger.debug(f"  ✅ Tier 2 PASS: {pos['symbol']}")
            
            logger.info(f"✅ Passed Tier 2 hard filters: {len(tier2_candidates)} positions")
            logger.info(f"🔍 Filtered Tier 2: {tier2_filtered} positions")
            
            # Now rank/sort Tier 2 candidates
            if tier2_candidates:
                logger.info(f"📊 Ranking {len(tier2_candidates)} positions by: {tier2_ranking.upper()}")
                
                if tier2_ranking == 'roc':
                    # Sort by ROC (highest first)
                    tier2_candidates.sort(key=lambda x: x['roc'], reverse=True)
                    logger.info("  Sorted by ROC (capital efficiency)")
                    
                elif tier2_ranking == 'premium':
                    # Sort by premium (highest income first)
                    tier2_candidates.sort(key=lambda x: x['premium_total'], reverse=True)
                    logger.info("  Sorted by Premium (highest income)")
                    
                elif tier2_ranking == 'ai_score':
                    # AI scoring (most sophisticated)
                    logger.info("  🤖 AI Scoring positions...")
                    # Will be done after import
                    pass
                
                else:  # 'balanced'
                    # Balanced score: ROC + Premium + IV
                    for pos in tier2_candidates:
                        pos['balanced_score'] = (
                            float(pos['roc']) * 0.4 +  # ROC weight: 40%
                            (float(pos['premium_total']) / 10) * 0.3 +  # Premium weight: 30%
                            float(pos['iv_rank']) * 100 * 0.3  # IV weight: 30%
                        )
                    tier2_candidates.sort(key=lambda x: x['balanced_score'], reverse=True)
                    logger.info("  Sorted by Balanced Score (ROC + Premium + IV)")
                
                # Select top N positions
                final_positions = tier2_candidates[:tier2_max_positions]
                logger.info(f"🎯 Selected TOP {len(final_positions)} positions for import")
            else:
                logger.warning("⚠️  No positions passed Tier 2 filters!")
                final_positions = []
        else:
            # Tier 2 disabled - use all Tier 1 positions
            logger.info("⏭️  Tier 2 filters disabled - using all Tier 1 positions")
            final_positions = tier1_passed[:max_positions]  # Respect max_positions
        
        logger.info("=" * 80)
        logger.info("💾 IMPORTING FINAL POSITIONS TO DATABASE")
        logger.info("=" * 80)
        
        # Now actually create the database records for final positions
        imported_ids = []
        for pos in final_positions:
            try:
                logger.debug(f"  💾 Importing: {pos['symbol']} (Premium: ${pos['premium_total']}, ROC: {pos['roc']*100:.1f}%)")
                logger.debug(f"       ESTIMATED for client review: Collect ${pos['premium_total']}, Risk ${pos['capital_required']}, {pos['roc']*100:.1f}% return")
                raw_data = _create_raw_data_from_mapped(pos['mapped_data'], strategy_type)
                imported_ids.append(raw_data.id)
            except Exception as e:
                logger.error(f"  ❌ Error importing {pos['symbol']}: {str(e)}")
                error_count += 1
        
        logger.info(f"✅ Successfully imported {len(imported_ids)} positions to database")
        logger.info("=" * 80)
        
        # Step 2: Convert to SuggestedPositions (if enabled)
        converted_ids = []
        if auto_convert and imported_ids:
            logger.info("🔄 Converting to SuggestedPositions...")
            converter = OptionPlayConverterService()
            for idx, raw_id in enumerate(imported_ids, 1):
                try:
                    raw_data = OptionPlayRawData.objects.get(id=raw_id)
                    suggestion = converter.convert_raw_to_suggestion(raw_data)
                    if suggestion:
                        converted_ids.append(suggestion.id)
                        logger.debug(f"  ✅ Converted {idx}/{len(imported_ids)}: {raw_data.symbol}")
                except Exception as e:
                    logger.error(f"  ❌ Conversion error for ID {raw_id}: {str(e)}")
                    continue
            
            logger.info(f"✅ Conversion complete: {len(converted_ids)}/{len(imported_ids)} positions converted")
        
        # Step 3: AI Score (if enabled)
        scored_count = 0
        if auto_score and converted_ids:
            logger.info("🤖 AI Scoring positions...")
            scorer = PositionScoringService()
            for idx, suggestion_id in enumerate(converted_ids, 1):
                try:
                    suggestion = SuggestedPosition.objects.get(id=suggestion_id)
                    
                    # Get the raw data to access IV rank
                    raw_data = OptionPlayRawData.objects.filter(
                        symbol=suggestion.symbol,
                        expiry=suggestion.expiration_date
                    ).first()
                    
                    # Build position data dict for AI scorer
                    # NOTE: AI scorer expects IV as percentage (0-100), but we store as decimal (0-1)
                    iv_rank_pct = (raw_data.iv_rank * 100) if raw_data and raw_data.iv_rank else None
                    
                    position_data = {
                        'symbol': suggestion.symbol,
                        'strategy': suggestion.get_strategy_display(),
                        'premium': suggestion.premium_collected or Decimal('0'),
                        'max_loss': suggestion.max_loss or Decimal('1'),
                        'dte': suggestion.dte,  # Use 'dte' field, not 'calculated_dte' property
                        'iv_rank': float(iv_rank_pct) if iv_rank_pct else None,  # Convert to percentage!
                        'days_to_earnings': None,
                        'volume': None,
                        'open_interest': None,
                    }
                    
                    # Score the position
                    score_result = scorer.score_position(position_data)
                    
                    # Update suggestion with AI score
                    # Convert Decimals to floats for JSON serialization
                    breakdown = score_result['breakdown']
                    if isinstance(breakdown, dict):
                        breakdown = {k: float(v) if isinstance(v, Decimal) else v for k, v in breakdown.items()}
                    
                    suggestion.ai_score = score_result['score']
                    suggestion.ai_rating = score_result['rating']
                    suggestion.ai_breakdown = breakdown  # Now JSON-serializable
                    suggestion.ai_recommendation = score_result['recommendation']
                    suggestion.ai_confidence_level = score_result['confidence']
                    suggestion.save()
                    
                    scored_count += 1
                    logger.debug(f"  ✅ Scored {idx}/{len(converted_ids)}: {suggestion.symbol} (Score: {score_result['score']}, Rating: {score_result['rating']})")
                    
                except Exception as e:
                    logger.error(f"  ❌ Scoring error for ID {suggestion_id}: {str(e)}")
                    continue
            
            logger.info(f"✅ AI Scoring complete: {scored_count}/{len(converted_ids)} positions scored")
        
        # Clear session
        logger.info("🧹 Clearing session data...")
        request.session.pop('csv_data', None)
        request.session.pop('csv_headers', None)
        request.session.pop('field_mapping', None)
        logger.info("✅ Session cleared")
        
        # Final summary
        logger.info("=" * 80)
        logger.info("🎉 FINAL SUMMARY (Two-Tier Filtering)")
        logger.info("=" * 80)
        if deleted_count > 0:
            logger.info(f"🗑️  Deleted (Replace Mode): {deleted_count}")
        if archived_count > 0:
            logger.info(f"🧹 Archived (Expired): {archived_count}")
        logger.info(f"Total Rows Processed: {len(csv_data)}")
        logger.info(f"")
        logger.info(f"TIER 1 (Quality):")
        logger.info(f"  ✅ Passed: {len(tier1_passed)} positions")
        logger.info(f"  🔍 Filtered: {tier1_filtered} positions")
        if tier2_enabled:
            logger.info(f"")
            logger.info(f"TIER 2 (Final Selection):")
            logger.info(f"  ✅ Passed: {len(final_positions)} positions")
            logger.info(f"  🔍 Filtered: {tier2_filtered} positions")
        logger.info(f"")
        logger.info(f"✅ Successfully Imported: {len(imported_ids)}")
        logger.info(f"🔄 Converted to Suggestions: {len(converted_ids)}")
        logger.info(f"🤖 AI Scored: {scored_count}")
        logger.info(f"❌ Errors: {error_count}")
        
        # Show Tier 1 filter breakdown
        if tier1_filtered > 0:
            logger.info("\n📊 TIER 1 FILTER BREAKDOWN:")
            logger.info(f"   Premium too low: {tier1_reasons['premium']}")
            logger.info(f"   IV Rank too low: {tier1_reasons['iv_rank']}")
            logger.info(f"   DTE too high: {tier1_reasons['dte']}")
            logger.info(f"   ROC too low: {tier1_reasons['roc']} (capital efficiency below {min_roc*100:.1f}%)")
            logger.info(f"   Symbol not allowed: {tier1_reasons['symbol']}")
        
        # Show Tier 2 filter breakdown
        if tier2_enabled and tier2_filtered > 0:
            logger.info("\n📊 TIER 2 FILTER BREAKDOWN:")
            logger.info(f"   Has earnings: {tier2_reasons['earnings']}")
            logger.info(f"   Not blue chip: {tier2_reasons['blue_chip']}")
            logger.info(f"   Stock price out of range: {tier2_reasons['stock_price']}")
            logger.info(f"   Too close to strike: {tier2_reasons['distance_otm']}")
            
            if rejected_samples:
                logger.info("\n❌ SAMPLE REJECTED POSITIONS (first 5):")
                for i, sample in enumerate(rejected_samples, 1):
                    logger.info(f"   {i}. {sample['symbol']}: Premium=${sample['premium']}, IV={sample['iv_rank']*100:.1f}%, DTE={sample['dte']}")
                    logger.info(f"       ROC: {sample['roc']*100:.1f}% (${sample['premium']} premium / ${sample['capital']} capital)")
                    logger.info(f"       Suggested {sample['spread_width']}-point spread (ESTIMATED for screening)")
                    logger.info(f"       Reasons: {', '.join(sample['reasons'])}")
            
            # Special note about ROC filtering
            if tier1_reasons['roc'] > 0:
                logger.info(f"\n💡 CAPITAL EFFICIENCY & CLIENT RISK DISCLOSURE:")
                logger.info(f"   {tier1_reasons['roc']} positions filtered for low Return on Capital (< {min_roc*100:.1f}%)")
                logger.info(f"   ROC = (Premium × 100) / Capital (contract values: 0.57 = 57%)")
                logger.info(f"   Example:")
                logger.info(f"      Good: $4/share ($400) on $700 spread = 0.57 ROC (57%) ✅")
                logger.info(f"      Poor: $2/share ($200) on $600 spread = 0.33 ROC (33%) ❌")
                logger.info(f"   ⚠️ NOTE: Estimates for screening. Actual execution prices will vary.")
                logger.info(f"   Lower ROC filter to see more positions (try 0.30-0.35)")
        
        logger.info("=" * 80)
        
        # Calculate near-miss positions if nothing was imported
        near_miss_positions = []
        if len(imported_ids) == 0 and tier1_filtered > 0:
            logger.info("🔍 No positions imported - calculating near-miss positions...")
            near_miss_positions = _find_near_miss_positions(
                rejected_samples, 
                min_premium, 
                min_iv, 
                max_dte, 
                min_roc
            )
            logger.info(f"✅ Found {len(near_miss_positions)} near-miss positions")
        
        # Show results
        context = {
            'imported_count': len(imported_ids),
            'tier1_passed': len(tier1_passed),
            'tier1_filtered': tier1_filtered,
            'tier2_enabled': tier2_enabled,
            'tier2_filtered': tier2_filtered,
            'error_count': error_count,
            'converted_count': len(converted_ids),
            'scored_count': scored_count,
            'auto_convert': auto_convert,
            'auto_score': auto_score,
            'deleted_count': deleted_count,
            'archived_count': archived_count,
            'import_mode': import_mode,
            'tier1_breakdown': tier1_reasons,
            'tier2_breakdown': tier2_reasons,
            'near_miss_positions': near_miss_positions,
            'title': 'CSV Upload - Complete'
        }
        
        logger.info("✅ Rendering Step 4 (Results)")
        return render(request, 'investing/managed/csv_upload_step4.html', context)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ CRITICAL ERROR IN IMPORT PROCESS")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("=" * 80)
        messages.error(request, f'Import error: {str(e)}')
        return redirect('investing:csv_upload_wizard')


# Helper functions

def _find_near_miss_positions(rejected_samples, min_premium, min_iv, max_dte, min_roc):
    """
    Find the best near-miss positions that came closest to passing filters
    
    Scores each position by how many filters it passed
    Returns top 2-3 with suggestions on how to adjust filters
    """
    if not rejected_samples:
        return []
    
    near_misses = []
    
    for sample in rejected_samples:
        # Calculate how many filters this position passed
        score = 0
        suggestions = []
        
        # Check premium
        if sample['premium'] >= min_premium:
            score += 1
        else:
            diff = min_premium - sample['premium']
            suggestions.append(f"Lower min premium by ${diff:.2f} (to ${sample['premium']:.2f})")
        
        # Check IV rank
        if sample['iv_rank'] >= min_iv:
            score += 1
        else:
            diff = min_iv - sample['iv_rank']
            suggestions.append(f"Lower min IV rank by {diff:.1f}% (to {sample['iv_rank']:.1f}%)")
        
        # Check DTE
        if sample['dte'] <= max_dte:
            score += 1
        else:
            diff = sample['dte'] - max_dte
            suggestions.append(f"Increase max DTE by {diff} days (to {sample['dte']} days)")
        
        # Check ROC
        if sample['roc'] >= min_roc:
            score += 1
        else:
            diff = min_roc - sample['roc']
            suggestions.append(f"Lower min ROC by {diff:.1f}% (to {sample['roc']:.1f}%)")
        
        # Add to near misses if it passed at least 2 out of 4 filters
        if score >= 2:
            near_misses.append({
                'symbol': sample['symbol'],
                'premium': sample['premium'],
                'iv_rank': sample['iv_rank'],
                'dte': sample['dte'],
                'roc': sample['roc'],
                'capital': sample['capital'],
                'spread_width': sample['spread_width'],
                'score': score,
                'reasons': sample['reasons'],
                'suggestions': suggestions
            })
    
    # Sort by score (best first), then by ROC (highest first)
    near_misses.sort(key=lambda x: (x['score'], x['roc']), reverse=True)
    
    # Return top 3
    return near_misses[:3]


def _calculate_spread_width(strike_price, width_choice='auto'):
    """
    Calculate optimal spread width based on strike price
    
    Industry standards:
    - $0-50: 3-5 points
    - $50-100: 5 points
    - $100-200: 5-7 points
    - $200+: 7-10 points
    """
    if width_choice != 'auto':
        try:
            return int(width_choice)
        except:
            pass
    
    # Auto-calculate based on strike
    if strike_price < 50:
        return 5
    elif strike_price < 100:
        return 5
    elif strike_price < 200:
        return 7
    else:
        return 10


def _clean_decimal_value(value_str):
    """
    Clean and convert string to Decimal, handling $, %, commas, spaces
    
    Note: Excel stores percentages as decimals (0.28 = 28%)
    We keep this format - don't convert!
    Filters should use decimal format too (0.35 instead of 35)
    """
    if not value_str:
        return Decimal('0')
    
    # Convert to string and clean
    cleaned = str(value_str).strip()
    # Remove $, %, commas
    cleaned = cleaned.replace('$', '').replace('%', '').replace(',', '').strip()
    
    # Handle empty or non-numeric
    if not cleaned or cleaned == '':
        return Decimal('0')
    
    try:
        return Decimal(cleaned)
    except (ValueError, TypeError):
        return Decimal('0')


def _clean_int_value(value_str):
    """Clean and convert string to int"""
    if not value_str:
        return 0
    
    cleaned = str(value_str).strip()
    # Remove $, %, commas
    cleaned = cleaned.replace('$', '').replace('%', '').replace(',', '').strip()
    
    if not cleaned or cleaned == '':
        return 0
    
    try:
        return int(float(cleaned))  # Use float first to handle decimals
    except (ValueError, TypeError):
        return 0


def _auto_map_columns(headers):
    """
    Intelligently auto-map CSV columns to model fields
    
    Returns dict: {csv_column: model_field}
    """
    mapping = {}
    
    for header in headers:
        header_lower = header.lower().strip()
        
        # Symbol
        if 'symbol' in header_lower and 'unique' not in header_lower:
            mapping[header] = 'symbol'
        
        # Prices
        elif 'stock price' in header_lower or 'underlying price' in header_lower:
            mapping[header] = 'price'
        elif 'mid price' in header_lower or 'premium' in header_lower and 'width' not in header_lower:
            mapping[header] = 'premium'
        
        # Strikes
        elif 'strike price' in header_lower or ('strike' in header_lower and 'distance' not in header_lower):
            mapping[header] = 'sell_strike'
        elif 'sell strike' in header_lower:
            mapping[header] = 'sell_strike'
        elif 'buy strike' in header_lower:
            mapping[header] = 'buy_strike'
        
        # Dates
        elif 'expir' in header_lower and 'days' not in header_lower:
            mapping[header] = 'expiry'
        elif 'days to expir' in header_lower or header_lower == 'dte':
            mapping[header] = 'dte'
        
        # Metrics
        elif 'iv rank' in header_lower or 'implied volatility rank' in header_lower:
            mapping[header] = 'iv_rank'
        elif 'annual' in header_lower and 'return' in header_lower:
            mapping[header] = 'annual_return'
        elif 'distance' in header_lower and 'strike' in header_lower:
            mapping[header] = 'distance_to_strike'
        elif 'width' in header_lower and 'prem' not in header_lower:
            mapping[header] = 'width'
        elif ('prem' in header_lower or 'premium') and 'width' in header_lower:
            mapping[header] = 'prem_width'
        
        # Earnings
        elif 'earnings flag' in header_lower:
            mapping[header] = 'earnings_flag'
        elif 'earnings date' in header_lower:
            mapping[header] = 'skip'  # We use earnings_flag, not date
        
        # Skip unnecessary columns
        elif any(skip_word in header_lower for skip_word in ['action', 'bid', 'ask', 'unique']):
            mapping[header] = 'skip'
        
        # Unknown - skip by default
        else:
            mapping[header] = 'skip'
    
    logger.info("🤖 Auto-mapped columns:")
    for csv_col, model_field in mapping.items():
        if model_field != 'skip':
            logger.info(f"   {csv_col} → {model_field}")
    
    skipped = [k for k, v in mapping.items() if v == 'skip']
    if skipped:
        logger.info(f"⏭️  Skipping columns: {', '.join(skipped)}")
    
    return mapping


def _read_excel_to_csv_string(excel_file, file_extension):
    """
    Read Excel file (.xlsx or .xls) and convert to CSV string format
    
    Handles:
    - Multiple sheets (reads first sheet)
    - Title rows (preserves them for header detection)
    - Data formatting
    """
    try:
        logger.info("📊 Reading Excel file with pandas...")
        
        # Lazy import pandas to avoid breaking local dev if not installed
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas library required for Excel file uploads. Please install: pip install pandas")
        
        # Read Excel with pandas (openpyxl engine for .xlsx)
        if file_extension == 'xlsx':
            df = pd.read_excel(excel_file, sheet_name=0, header=None, engine='openpyxl')
            logger.info(f"✅ Excel (.xlsx) loaded: {len(df)} rows, {len(df.columns)} columns")
        else:  # xls (legacy format)
            # Try reading with xlrd (if available), otherwise suggest conversion
            try:
                df = pd.read_excel(excel_file, sheet_name=0, header=None, engine='xlrd')
                logger.info(f"✅ Excel (.xls) loaded: {len(df)} rows, {len(df.columns)} columns")
            except ImportError:
                logger.error("❌ xlrd not installed - cannot read .xls files")
                raise ValueError("Legacy .xls format not supported. Please save as .xlsx in Excel and try again.")
        
        # Convert DataFrame to CSV string
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, header=False)
        csv_string = csv_buffer.getvalue()
        
        logger.info(f"✅ Converted to CSV format ({len(csv_string)} characters)")
        logger.info(f"📊 Preview: {csv_string[:200]}...")  # First 200 chars
        
        return csv_string
        
    except ValueError as e:
        # Re-raise ValueError for user-friendly messages
        raise
    except ImportError as e:
        # Re-raise ImportError for library issues
        raise
    except Exception as e:
        logger.error(f"❌ Error reading Excel file: {str(e)}", exc_info=True)
        raise


def _detect_strategy_type(filename, headers):
    """Auto-detect strategy type from filename or headers"""
    filename_lower = filename.lower()
    
    if 'credit' in filename_lower or 'spread' in filename_lower:
        return 'credit_spread'
    elif 'short_put' in filename_lower or 'put' in filename_lower:
        return 'short_put'
    elif 'covered_call' in filename_lower or 'call' in filename_lower:
        return 'covered_call'
    
    # Check headers
    if any('spread' in h.lower() for h in headers):
        return 'credit_spread'
    
    return 'short_put'  # Default


def _calculate_csv_stats(csv_data, field_mapping):
    """Calculate statistics for filter suggestions"""
    premiums = []
    ivs = []
    dtes = []
    symbols = set()
    
    # Get mapped field names
    premium_field = next((k for k, v in field_mapping.items() if v == 'premium'), None)
    iv_field = next((k for k, v in field_mapping.items() if v == 'iv_rank'), None)
    dte_field = next((k for k, v in field_mapping.items() if v == 'dte'), None)
    symbol_field = next((k for k, v in field_mapping.items() if v == 'symbol'), None)
    
    for row in csv_data:
        try:
            if premium_field and row.get(premium_field):
                value = str(row[premium_field]).replace('$', '').replace(',', '').strip()
                if value:
                    premiums.append(Decimal(value))
            
            if iv_field and row.get(iv_field):
                value = str(row[iv_field]).replace('%', '').strip()
                if value:
                    # Keep Excel decimal format (0.28 = 28%)
                    ivs.append(Decimal(value))
            
            if dte_field and row.get(dte_field):
                value = str(row[dte_field]).strip()
                if value:
                    dtes.append(int(float(value)))
            
            if symbol_field and row.get(symbol_field):
                value = str(row[symbol_field]).strip().upper()
                if value:
                    symbols.add(value)
        except Exception as e:
            logger.debug(f"    Error calculating stats for row: {e}")
            continue
    
    return {
        'avg_premium': sum(premiums) / len(premiums) if premiums else 0,
        'min_premium': min(premiums) if premiums else 0,
        'max_premium': max(premiums) if premiums else 0,
        'avg_iv': sum(ivs) / len(ivs) if ivs else 0,
        'avg_dte': sum(dtes) / len(dtes) if dtes else 0,
        'unique_symbols': len(symbols),
        'symbols_list': sorted(list(symbols))[:20]  # Top 20
    }


def _create_raw_data_from_mapped(mapped_data, strategy_type):
    """Create OptionPlayRawData from mapped fields"""
    
    # Parse date
    expiry_str = mapped_data.get('expiry', '')
    try:
        expiry = datetime.strptime(expiry_str, '%Y-%m-%d').date()
    except:
        try:
            expiry = datetime.strptime(expiry_str, '%m/%d/%Y').date()
        except:
            expiry = date.today()
    
    # Create raw data - use helper functions to clean values
    # Note: Excel percentage format (0.28 = 28%) is kept as-is
    raw_data = OptionPlayRawData.objects.create(
        strategy_type=strategy_type,
        symbol=mapped_data.get('symbol', '').upper().strip(),
        stock_price=_clean_decimal_value(mapped_data.get('price', '0')),
        sell_strike=_clean_decimal_value(mapped_data.get('sell_strike', '0')),
        buy_strike=_clean_decimal_value(mapped_data.get('buy_strike', '0')) if mapped_data.get('buy_strike') else None,
        premium=_clean_decimal_value(mapped_data.get('premium', '0')),
        expiry=expiry,
        days_to_expiry=_clean_int_value(mapped_data.get('dte', '30')),
        iv_rank=_clean_decimal_value(mapped_data.get('iv_rank', '0')),  # Excel: 0.28 (28%)
        annualized_return=_clean_decimal_value(mapped_data.get('annual_return', '0')),  # Excel: 1.29 (129%)
        distance_to_strike=_clean_decimal_value(mapped_data.get('distance_to_strike', '0')),  # Excel: -0.03 (-3%)
        width=_clean_decimal_value(mapped_data.get('width', '0')) if mapped_data.get('width') else None,
        prem_width_ratio=_clean_decimal_value(mapped_data.get('prem_width', '0')) if mapped_data.get('prem_width') else None,
        earnings_flag=mapped_data.get('earnings_flag', 'N').strip().upper(),  # CharField: 'Y' or 'N'
        upload_notes=f"Imported from CSV - estimated spread for client review"  # Correct field name
    )
    
    return raw_data

