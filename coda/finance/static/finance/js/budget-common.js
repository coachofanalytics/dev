/**
 * Budget System Common JavaScript
 * Phase 4: Consolidated JS for all budget templates
 * 
 * Provides:
 * - Tab navigation
 * - Department filtering
 * - Form validation
 * - Chart utilities
 * - AJAX helpers
 */

(function($) {
    'use strict';
    
    // ================================================================
    // BUDGET DASHBOARD UTILITIES
    // ================================================================
    
    const BudgetDashboard = {
        
        /**
         * Initialize dashboard functionality
         */
        init: function() {
            console.log('Budget Dashboard initialized');
            this.setupDepartmentFilter();
            this.setupTabNavigation();
            this.setupFormValidation();
            this.initializeCharts();
        },
        
        /**
         * Setup department filter auto-submit
         */
        setupDepartmentFilter: function() {
            $('#department_filter').on('change', function() {
                $(this).closest('form').submit();
            });
        },
        
        /**
         * Setup tab navigation with history
         */
        setupTabNavigation: function() {
            $('.nav-tabs .nav-link').on('click', function(e) {
                const tab = $(this).attr('href').split('tab=')[1];
                if (tab) {
                    console.log('Switching to tab:', tab);
                }
            });
        },
        
        /**
         * Setup form validation
         */
        setupFormValidation: function() {
            $('form[data-validate]').on('submit', function(e) {
                let isValid = true;
                
                $(this).find('[required]').each(function() {
                    if (!$(this).val()) {
                        isValid = false;
                        $(this).addClass('is-invalid');
                    } else {
                        $(this).removeClass('is-invalid');
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    alert('Please fill in all required fields');
                }
            });
        },
        
        /**
         * Initialize charts if Chart.js is available
         */
        initializeCharts: function() {
            if (typeof Chart !== 'undefined') {
                console.log('Chart.js available - charts initialized');
            }
        }
    };
    
    // ================================================================
    // BUDGET ESTIMATION UTILITIES
    // ================================================================
    
    const BudgetEstimation = {
        
        /**
         * Calculate budget estimate
         */
        calculateEstimate: function(baseAmount, timeframe, periods) {
            const multipliers = {
                'weekly': 0.23,      // ~1 week = 23% of month
                'monthly': 1,
                'quarterly': 3,
                'yearly': 12,
                'multi_year': 12
            };
            
            const multiplier = multipliers[timeframe] || 1;
            return baseAmount * multiplier * periods;
        },
        
        /**
         * Format currency
         */
        formatCurrency: function(amount) {
            return '$' + parseFloat(amount).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        },
        
        /**
         * Calculate confidence indicator
         */
        getConfidenceIndicator: function(score) {
            if (score >= 0.9) return { level: 'high', color: 'success', icon: 'check-circle' };
            if (score >= 0.7) return { level: 'medium', color: 'warning', icon: 'exclamation-circle' };
            return { level: 'low', color: 'danger', icon: 'exclamation-triangle' };
        }
    };
    
    // ================================================================
    // AJAX HELPERS
    // ================================================================
    
    const BudgetAjax = {
        
        /**
         * Get CSRF token
         */
        getCSRFToken: function() {
            return $('[name=csrfmiddlewaretoken]').val() || 
                   $('meta[name="csrf-token"]').attr('content');
        },
        
        /**
         * Standard AJAX request
         */
        request: function(url, method, data, successCallback, errorCallback) {
            $.ajax({
                url: url,
                method: method || 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                data: method === 'POST' ? JSON.stringify(data) : data,
                success: function(response) {
                    if (successCallback) successCallback(response);
                },
                error: function(xhr, status, error) {
                    console.error('AJAX Error:', error);
                    if (errorCallback) errorCallback(xhr, status, error);
                }
            });
        },
        
        /**
         * Load tab content via AJAX (for future optimization)
         */
        loadTab: function(tabName, container) {
            this.request(
                `/finance/api/budget-tab/${tabName}/`,
                'GET',
                null,
                function(response) {
                    $(container).html(response.html);
                },
                function() {
                    $(container).html('<div class="alert alert-danger">Error loading tab</div>');
                }
            );
        }
    };
    
    // ================================================================
    // FORM UTILITIES
    // ================================================================
    
    const BudgetForms = {
        
        /**
         * Auto-calculate budget totals
         */
        setupAutoCalculation: function() {
            $('[data-auto-calculate]').on('change', function() {
                const form = $(this).closest('form');
                const quantity = parseFloat(form.find('[name="quantity"]').val()) || 0;
                const unitPrice = parseFloat(form.find('[name="unit_price"]').val()) || 0;
                const cases = parseFloat(form.find('[name="cases"]').val()) || 1;
                
                const total = quantity * unitPrice * cases;
                form.find('[data-total-display]').text(BudgetEstimation.formatCurrency(total));
            });
        },
        
        /**
         * Timeframe period adjuster
         */
        setupPeriodAdjuster: function() {
            $('#timeframe').on('change', function() {
                const timeframe = $(this).val();
                const periodsInput = $('#periods');
                
                // Adjust default periods based on timeframe
                const defaults = {
                    'weekly': 4,
                    'monthly': 3,
                    'quarterly': 4,
                    'yearly': 1,
                    'multi_year': 2
                };
                
                periodsInput.val(defaults[timeframe] || 1);
            });
        }
    };
    
    // ================================================================
    // DEPRECATION NOTICES
    // ================================================================
    
    const DeprecationNotice = {
        
        /**
         * Show deprecation notice with redirect suggestion
         */
        show: function(newUrl, message) {
            const notice = $(`
                <div class="alert alert-warning alert-dismissible fade show deprecation-notice" role="alert">
                    <h5><i class="fas fa-exclamation-triangle"></i> This page has been updated</h5>
                    <p>${message || 'This view has been replaced by our new unified dashboard.'}</p>
                    <a href="${newUrl}" class="btn btn-primary btn-sm mt-2">
                        <i class="fas fa-arrow-right"></i> Go to New Dashboard
                    </a>
                    <button type="button" class="close" data-dismiss="alert">
                        <span>&times;</span>
                    </button>
                </div>
            `);
            
            $('.container-fluid').prepend(notice);
        }
    };
    
    // ================================================================
    // INITIALIZATION
    // ================================================================
    
    $(document).ready(function() {
        // Initialize dashboard
        if ($('[data-budget-dashboard]').length) {
            BudgetDashboard.init();
        }
        
        // Setup form utilities
        BudgetForms.setupAutoCalculation();
        BudgetForms.setupPeriodAdjuster();
        
        // Log initialization
        console.log('Budget Common JS loaded successfully');
    });
    
    // ================================================================
    // EXPORT TO GLOBAL SCOPE
    // ================================================================
    
    window.BudgetDashboard = BudgetDashboard;
    window.BudgetEstimation = BudgetEstimation;
    window.BudgetAjax = BudgetAjax;
    window.BudgetForms = BudgetForms;
    window.DeprecationNotice = DeprecationNotice;
    
})(jQuery);


