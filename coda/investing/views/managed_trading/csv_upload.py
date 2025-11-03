"""
CSV Upload Wizard for OptionPlay Data

Multi-step wizard with preview, field mapping, quality filters, and AI scoring.
"""

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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
            
            # Get existing data counts for cleanup context
            from django.utils import timezone
            existing_total = OptionPlayRawData.objects.count()
            existing_expired = OptionPlayRawData.objects.filter(expiry__lt=timezone.now().date()).count()
            existing_active = existing_total - existing_expired
            
            logger.info(f"📊 Existing data: {existing_total} total ({existing_active} active, {existing_expired} expired)")
            
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
            
            context = {
                'headers': headers,
                'preview_rows': preview_rows[:5],  # First 5 for preview
                'total_rows': len(all_rows),
                'filename': csv_file.name,
                'strategy_type': strategy_type,
                'title': 'CSV Upload - Step 2: Confirm & Filter',
                'skipped_rows': header_row_index,
                'field_mapping': field_mapping,
                'stats': stats,
                'existing_total': existing_total,
                'existing_active': existing_active,
                'existing_expired': existing_expired,
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
        
        # Get filter parameters
        logger.info("🔧 Reading filter parameters...")
        min_premium = Decimal(request.POST.get('min_premium', '0'))
        min_iv = Decimal(request.POST.get('min_iv', '0'))
        max_dte = int(request.POST.get('max_dte', '365'))
        max_positions = int(request.POST.get('max_positions', '100'))
        auto_convert = request.POST.get('auto_convert') == 'on'
        auto_score = request.POST.get('auto_score') == 'on'
        symbol_filter = request.POST.get('symbol_filter', '').strip()
        import_mode = request.POST.get('import_mode', 'add')  # add, replace, cleanup
        
        logger.info("=" * 80)
        logger.info("📊 IMPORT SETTINGS")
        logger.info("=" * 80)
        logger.info(f"Import Mode: {import_mode.upper()}")
        logger.info(f"Min Premium: ${min_premium}")
        logger.info(f"Min IV Rank: {min_iv}%")
        logger.info(f"Max DTE: {max_dte} days")
        logger.info(f"Max Positions: {max_positions}")
        logger.info(f"Auto-Convert: {auto_convert}")
        logger.info(f"Auto-Score: {auto_score}")
        logger.info(f"Symbol Filter: {symbol_filter or 'None (all symbols)'}")
        logger.info("=" * 80)
        
        # Parse symbol filter
        if symbol_filter:
            allowed_symbols = [s.strip().upper() for s in symbol_filter.split(',')]
            logger.info(f"✅ Allowed symbols: {allowed_symbols}")
        else:
            allowed_symbols = None
            logger.info("✅ All symbols allowed")
        
        # Handle data cleanup based on import mode
        deleted_count = 0
        archived_count = 0
        
        if import_mode == 'replace':
            logger.info("🗑️  REPLACE MODE: Deleting ALL old OptionPlayRawData...")
            old_count = OptionPlayRawData.objects.count()
            OptionPlayRawData.objects.all().delete()
            deleted_count = old_count
            logger.info(f"✅ Deleted {deleted_count} old positions")
            
        elif import_mode == 'cleanup':
            logger.info("🧹 CLEANUP MODE: Archiving expired positions...")
            from django.utils import timezone
            
            # Delete expired positions (expiry in the past)
            expired = OptionPlayRawData.objects.filter(expiry__lt=timezone.now().date())
            expired_count = expired.count()
            
            if expired_count > 0:
                logger.info(f"   Found {expired_count} expired positions")
                expired.delete()
                archived_count = expired_count
                logger.info(f"✅ Archived {archived_count} expired positions")
            else:
                logger.info("   No expired positions found")
        
        else:  # 'add' mode
            logger.info("➕ ADD MODE: Keeping existing data, adding new positions")
        
        # Import with filters
        logger.info("📥 Starting import process...")
        imported_ids = []
        filtered_count = 0
        error_count = 0
        
        # Filter debugging
        filter_reasons = {
            'premium': 0,
            'iv_rank': 0,
            'dte': 0,
            'symbol': 0,
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
                iv_rank_val = _clean_decimal_value(iv_rank_str)
                dte = _clean_int_value(dte_str)
                
                # Filter checks with detailed tracking
                filter_failed = False
                filter_reason = []
                
                if premium < min_premium:
                    filter_reasons['premium'] += 1
                    filter_reason.append(f"Premium ${premium} < ${min_premium}")
                    filter_failed = True
                
                if iv_rank_val < min_iv:
                    filter_reasons['iv_rank'] += 1
                    filter_reason.append(f"IV {iv_rank_val}% < {min_iv}%")
                    filter_failed = True
                
                if dte > max_dte:
                    filter_reasons['dte'] += 1
                    filter_reason.append(f"DTE {dte} > {max_dte}")
                    filter_failed = True
                
                if allowed_symbols and symbol not in allowed_symbols:
                    filter_reasons['symbol'] += 1
                    filter_reason.append(f"Symbol {symbol} not allowed")
                    filter_failed = True
                
                if len(imported_ids) >= max_positions:
                    filter_failed = True
                    filter_reason.append(f"Max positions reached ({max_positions})")
                
                if filter_failed:
                    filtered_count += 1
                    # Store first 5 rejections for debugging
                    if len(rejected_samples) < 5:
                        rejected_samples.append({
                            'symbol': symbol,
                            'premium': premium,
                            'iv_rank': iv_rank_val,
                            'dte': dte,
                            'reasons': filter_reason
                        })
                    continue
                
                # Create OptionPlayRawData
                logger.debug(f"  ✅ Row {idx}: Importing {symbol} (Premium: ${premium})")
                raw_data = _create_raw_data_from_mapped(mapped_data, strategy_type)
                imported_ids.append(raw_data.id)
                
                # Progress logging
                if idx % 10 == 0:
                    logger.info(f"  📊 Progress: {idx}/{len(csv_data)} rows processed, {len(imported_ids)} imported")
                
            except Exception as e:
                logger.error(f"  ❌ Row {idx}: Error importing - {str(e)}")
                error_count += 1
                continue
        
        logger.info("=" * 80)
        logger.info("📊 IMPORT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✅ Imported: {len(imported_ids)} positions")
        logger.info(f"🔍 Filtered: {filtered_count} positions")
        logger.info(f"❌ Errors: {error_count} positions")
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
                    scored = scorer.score_position(suggestion)
                    if scored and scored.ai_score:
                        scored_count += 1
                        logger.debug(f"  ✅ Scored {idx}/{len(converted_ids)}: {suggestion.symbol} (Score: {scored.ai_score})")
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
        logger.info("🎉 FINAL SUMMARY")
        logger.info("=" * 80)
        if deleted_count > 0:
            logger.info(f"🗑️  Deleted (Replace Mode): {deleted_count}")
        if archived_count > 0:
            logger.info(f"🧹 Archived (Expired): {archived_count}")
        logger.info(f"Total Rows Processed: {len(csv_data)}")
        logger.info(f"✅ Successfully Imported: {len(imported_ids)}")
        logger.info(f"🔄 Converted to Suggestions: {len(converted_ids)}")
        logger.info(f"🤖 AI Scored: {scored_count}")
        logger.info(f"🔍 Filtered Out: {filtered_count}")
        logger.info(f"❌ Errors: {error_count}")
        
        # Show filter breakdown
        if filtered_count > 0:
            logger.info("\n📊 FILTER BREAKDOWN:")
            logger.info(f"   Premium too low: {filter_reasons['premium']}")
            logger.info(f"   IV Rank too low: {filter_reasons['iv_rank']}")
            logger.info(f"   DTE too high: {filter_reasons['dte']}")
            logger.info(f"   Symbol not allowed: {filter_reasons['symbol']}")
            
            if rejected_samples:
                logger.info("\n❌ SAMPLE REJECTED POSITIONS (first 5):")
                for i, sample in enumerate(rejected_samples, 1):
                    logger.info(f"   {i}. {sample['symbol']}: Premium=${sample['premium']}, IV={sample['iv_rank']}%, DTE={sample['dte']}")
                    logger.info(f"      Reasons: {', '.join(sample['reasons'])}")
        
        logger.info("=" * 80)
        
        # Show results
        context = {
            'imported_count': len(imported_ids),
            'filtered_count': filtered_count,
            'error_count': error_count,
            'converted_count': len(converted_ids),
            'scored_count': scored_count,
            'auto_convert': auto_convert,
            'auto_score': auto_score,
            'deleted_count': deleted_count,
            'archived_count': archived_count,
            'import_mode': import_mode,
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

def _clean_decimal_value(value_str):
    """Clean and convert string to Decimal, handling $, %, commas, spaces"""
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
    raw_data = OptionPlayRawData.objects.create(
        strategy_type=strategy_type,
        symbol=mapped_data.get('symbol', '').upper().strip(),
        underlying_price=_clean_decimal_value(mapped_data.get('price', '0')),
        sell_strike=_clean_decimal_value(mapped_data.get('sell_strike', '0')),
        buy_strike=_clean_decimal_value(mapped_data.get('buy_strike', '0')) if mapped_data.get('buy_strike') else None,
        premium=_clean_decimal_value(mapped_data.get('premium', '0')),
        expiry=expiry,
        dte=_clean_int_value(mapped_data.get('dte', '30')),
        iv_rank=_clean_decimal_value(mapped_data.get('iv_rank', '0')),
        annual_return=_clean_decimal_value(mapped_data.get('annual_return', '0')),
        distance_to_strike=_clean_decimal_value(mapped_data.get('distance_to_strike', '0')),
        width=_clean_decimal_value(mapped_data.get('width', '0')) if mapped_data.get('width') else None,
        premium_to_width_ratio=_clean_decimal_value(mapped_data.get('prem_width', '0')) if mapped_data.get('prem_width') else None,
        earnings_flag=mapped_data.get('earnings_flag', 'N').strip().upper() == 'Y',
        notes=f"Imported from CSV"
    )
    
    return raw_data

