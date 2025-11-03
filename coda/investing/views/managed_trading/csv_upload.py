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
        if not csv_file.name.endswith('.csv'):
            logger.error(f"❌ Invalid file type: {csv_file.name}")
            messages.error(request, 'Please upload a CSV file')
            return render(request, 'investing/managed/csv_upload_step1.html')
        
        logger.info("✅ File type validated (CSV)")
        
        try:
            logger.info("📖 Reading CSV file...")
            
            # Read CSV
            file_data = csv_file.read().decode('utf-8')
            logger.info(f"✅ File decoded successfully ({len(file_data)} characters)")
            
            csv_reader = csv.DictReader(io.StringIO(file_data))
            
            # Get headers and preview data
            headers = csv_reader.fieldnames
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
            
            # Detect strategy type from filename or first row
            logger.info("🔍 Detecting strategy type...")
            strategy_type = _detect_strategy_type(csv_file.name, headers)
            request.session['strategy_type'] = strategy_type
            logger.info(f"✅ Strategy detected: {strategy_type}")
            
            logger.info("=" * 80)
            logger.info("📊 UPLOAD SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Filename: {csv_file.name}")
            logger.info(f"Size: {csv_file.size / 1024:.2f} KB")
            logger.info(f"Rows: {total_rows}")
            logger.info(f"Columns: {len(headers)}")
            logger.info(f"Strategy: {strategy_type}")
            logger.info("=" * 80)
            
            context = {
                'headers': headers,
                'preview_rows': preview_rows,
                'total_rows': len(all_rows),
                'filename': csv_file.name,
                'strategy_type': strategy_type,
                'title': 'CSV Upload - Step 2: Preview & Map Fields'
            }
            
            logger.info("✅ Rendering Step 2 (Preview & Map)")
            return render(request, 'investing/managed/csv_upload_step2.html', context)
            
        except UnicodeDecodeError as e:
            logger.error(f"❌ Unicode decode error: {str(e)}")
            logger.error("💡 Tip: Try saving the CSV with UTF-8 encoding")
            messages.error(request, f'Error reading CSV (encoding issue): {str(e)}. Try saving with UTF-8 encoding.')
            return render(request, 'investing/managed/csv_upload_step1.html')
        except csv.Error as e:
            logger.error(f"❌ CSV parsing error: {str(e)}")
            messages.error(request, f'Error parsing CSV: {str(e)}')
            return render(request, 'investing/managed/csv_upload_step1.html')
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
            messages.error(request, f'Error reading CSV: {str(e)}')
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
        
        logger.info("=" * 80)
        logger.info("📊 FILTER SETTINGS")
        logger.info("=" * 80)
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
        
        # Import with filters
        logger.info("📥 Starting import process...")
        imported_ids = []
        filtered_count = 0
        error_count = 0
        
        for idx, row_data in enumerate(csv_data, 1):
            try:
                # Map fields
                mapped_data = {}
                for csv_field, model_field in field_mapping.items():
                    value = row_data.get(csv_field, '').strip()
                    mapped_data[model_field] = value
                
                # Apply quality filters
                premium = Decimal(mapped_data.get('premium', '0') or '0')
                iv = Decimal(mapped_data.get('iv_rank', '0') or '0')
                dte = int(mapped_data.get('dte', '365') or '365')
                symbol = mapped_data.get('symbol', '').upper()
                
                # Filter checks
                if premium < min_premium:
                    filtered_count += 1
                    continue
                if iv < min_iv:
                    filtered_count += 1
                    continue
                if dte > max_dte:
                    filtered_count += 1
                    continue
                if allowed_symbols and symbol not in allowed_symbols:
                    filtered_count += 1
                    continue
                if len(imported_ids) >= max_positions:
                    filtered_count += 1
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
        logger.info(f"Total Rows Processed: {len(csv_data)}")
        logger.info(f"✅ Successfully Imported: {len(imported_ids)}")
        logger.info(f"🔄 Converted to Suggestions: {len(converted_ids)}")
        logger.info(f"🤖 AI Scored: {scored_count}")
        logger.info(f"🔍 Filtered Out: {filtered_count}")
        logger.info(f"❌ Errors: {error_count}")
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
    
    for row in csv_data:
        try:
            # Get mapped fields
            premium_field = next((k for k, v in field_mapping.items() if v == 'premium'), None)
            iv_field = next((k for k, v in field_mapping.items() if v == 'iv_rank'), None)
            dte_field = next((k for k, v in field_mapping.items() if v == 'dte'), None)
            symbol_field = next((k for k, v in field_mapping.items() if v == 'symbol'), None)
            
            if premium_field and row.get(premium_field):
                premiums.append(Decimal(row[premium_field].replace('$', '').strip()))
            if iv_field and row.get(iv_field):
                ivs.append(Decimal(row[iv_field].replace('%', '').strip()))
            if dte_field and row.get(dte_field):
                dtes.append(int(row[dte_field]))
            if symbol_field and row.get(symbol_field):
                symbols.add(row[symbol_field].strip().upper())
        except:
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
    
    # Create raw data
    raw_data = OptionPlayRawData.objects.create(
        strategy_type=strategy_type,
        symbol=mapped_data.get('symbol', '').upper(),
        underlying_price=Decimal(mapped_data.get('price', '0') or '0'),
        sell_strike=Decimal(mapped_data.get('sell_strike', '0') or '0'),
        buy_strike=Decimal(mapped_data.get('buy_strike', '0') or '0') if mapped_data.get('buy_strike') else None,
        premium=Decimal(mapped_data.get('premium', '0') or '0'),
        expiry=expiry,
        dte=int(mapped_data.get('dte', '30') or '30'),
        iv_rank=Decimal(mapped_data.get('iv_rank', '0') or '0'),
        annual_return=Decimal(mapped_data.get('annual_return', '0') or '0'),
        distance_to_strike=Decimal(mapped_data.get('distance_to_strike', '0') or '0'),
        width=Decimal(mapped_data.get('width', '0') or '0') if mapped_data.get('width') else None,
        premium_to_width_ratio=Decimal(mapped_data.get('prem_width', '0') or '0') if mapped_data.get('prem_width') else None,
        earnings_flag=mapped_data.get('earnings_flag', 'N') == 'Y',
        notes=f"Imported from CSV: {request.session.get('csv_filename', 'unknown')}"
    )
    
    return raw_data

