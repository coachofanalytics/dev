"""
Financial Utilities

This module contains utility functions for general financial operations
including calculations, validations, and financial data processing.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q
from decimal import Decimal
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import logging
import requests
from mail.custom_email import send_email

logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()


class FinancialUtils:
    """Utility class for general financial operations."""
    
    @staticmethod
    def calculate_interest(principal, rate, time_period, compounding_frequency=12):
        """
        Calculate compound interest for a loan or investment.
        
        Args:
            principal: Initial amount
            rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
            time_period: Time period in years
            compounding_frequency: Number of times interest is compounded per year
        
        Returns:
            Dictionary with interest calculation details
        """
        try:
            principal = float(principal)
            rate = float(rate)
            time_period = float(time_period)
            compounding_frequency = int(compounding_frequency)
            
            # Compound interest formula: A = P(1 + r/n)^(nt)
            amount = principal * (1 + rate / compounding_frequency) ** (compounding_frequency * time_period)
            interest = amount - principal
            
            return {
                'principal': principal,
                'rate': rate,
                'time_period': time_period,
                'compounding_frequency': compounding_frequency,
                'final_amount': amount,
                'interest_amount': interest,
                'interest_percentage': (interest / principal) * 100 if principal > 0 else 0,
            }
            
        except Exception as e:
            logger.error(f"Error calculating interest: {e}")
            return {
                'principal': 0,
                'rate': 0,
                'time_period': 0,
                'compounding_frequency': 12,
                'final_amount': 0,
                'interest_amount': 0,
                'interest_percentage': 0,
            }

    @staticmethod
    def calculate_loan_payment(principal, annual_rate, years):
        """
        Calculate monthly loan payment using the standard loan payment formula.
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (as decimal)
            years: Loan term in years
        
        Returns:
            Dictionary with payment calculation details
        """
        try:
            principal = float(principal)
            annual_rate = float(annual_rate)
            years = float(years)
            
            # Monthly interest rate
            monthly_rate = annual_rate / 12
            
            # Number of payments
            num_payments = years * 12
            
            # Monthly payment calculation: P * [r(1+r)^n] / [(1+r)^n - 1]
            if monthly_rate > 0:
                monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_payment = principal / num_payments
            
            total_payment = monthly_payment * num_payments
            total_interest = total_payment - principal
            
            return {
                'principal': principal,
                'annual_rate': annual_rate,
                'monthly_rate': monthly_rate,
                'years': years,
                'num_payments': num_payments,
                'monthly_payment': monthly_payment,
                'total_payment': total_payment,
                'total_interest': total_interest,
                'interest_percentage': (total_interest / principal) * 100 if principal > 0 else 0,
            }
            
        except Exception as e:
            logger.error(f"Error calculating loan payment: {e}")
            return {
                'principal': 0,
                'annual_rate': 0,
                'monthly_rate': 0,
                'years': 0,
                'num_payments': 0,
                'monthly_payment': 0,
                'total_payment': 0,
                'total_interest': 0,
                'interest_percentage': 0,
            }

    @staticmethod
    def calculate_amortization_schedule(principal, annual_rate, years):
        """
        Calculate amortization schedule for a loan.
        
        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (as decimal)
            years: Loan term in years
        
        Returns:
            List of dictionaries with payment schedule details
        """
        try:
            payment_calc = FinancialUtils.calculate_loan_payment(principal, annual_rate, years)
            monthly_payment = payment_calc['monthly_payment']
            monthly_rate = payment_calc['monthly_rate']
            num_payments = payment_calc['num_payments']
            
            schedule = []
            remaining_balance = principal
            
            for payment_num in range(1, int(num_payments) + 1):
                # Interest payment for this month
                interest_payment = remaining_balance * monthly_rate
                
                # Principal payment for this month
                principal_payment = monthly_payment - interest_payment
                
                # Update remaining balance
                remaining_balance -= principal_payment
                
                # Ensure remaining balance doesn't go negative
                if remaining_balance < 0:
                    remaining_balance = 0
                
                schedule.append({
                    'payment_number': payment_num,
                    'payment_amount': monthly_payment,
                    'principal_payment': principal_payment,
                    'interest_payment': interest_payment,
                    'remaining_balance': remaining_balance,
                })
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error calculating amortization schedule: {e}")
            return []

    @staticmethod
    def calculate_investment_return(initial_investment, final_value, time_period_years):
        """
        Calculate investment return metrics.
        
        Args:
            initial_investment: Initial investment amount
            final_value: Final investment value
            time_period_years: Investment period in years
        
        Returns:
            Dictionary with return calculation details
        """
        try:
            initial_investment = float(initial_investment)
            final_value = float(final_value)
            time_period_years = float(time_period_years)
            
            # Total return
            total_return = final_value - initial_investment
            
            # Return percentage
            return_percentage = (total_return / initial_investment) * 100 if initial_investment > 0 else 0
            
            # Annualized return (compound annual growth rate)
            if time_period_years > 0 and initial_investment > 0:
                annualized_return = ((final_value / initial_investment) ** (1 / time_period_years)) - 1
                annualized_return_percentage = annualized_return * 100
            else:
                annualized_return = 0
                annualized_return_percentage = 0
            
            return {
                'initial_investment': initial_investment,
                'final_value': final_value,
                'time_period_years': time_period_years,
                'total_return': total_return,
                'return_percentage': return_percentage,
                'annualized_return': annualized_return,
                'annualized_return_percentage': annualized_return_percentage,
            }
            
        except Exception as e:
            logger.error(f"Error calculating investment return: {e}")
            return {
                'initial_investment': 0,
                'final_value': 0,
                'time_period_years': 0,
                'total_return': 0,
                'return_percentage': 0,
                'annualized_return': 0,
                'annualized_return_percentage': 0,
            }

    @staticmethod
    def calculate_debt_to_income_ratio(monthly_debt_payments, monthly_income):
        """
        Calculate debt-to-income ratio.
        
        Args:
            monthly_debt_payments: Total monthly debt payments
            monthly_income: Monthly income
        
        Returns:
            Dictionary with DTI calculation details
        """
        try:
            monthly_debt_payments = float(monthly_debt_payments)
            monthly_income = float(monthly_income)
            
            if monthly_income <= 0:
                return {
                    'monthly_debt_payments': monthly_debt_payments,
                    'monthly_income': monthly_income,
                    'dti_ratio': 0,
                    'dti_percentage': 0,
                    'status': 'invalid_income',
                    'recommendation': 'Monthly income must be greater than zero.',
                }
            
            dti_ratio = monthly_debt_payments / monthly_income
            dti_percentage = dti_ratio * 100
            
            # Determine status based on DTI ratio
            if dti_percentage <= 20:
                status = 'excellent'
                recommendation = 'Excellent debt-to-income ratio. You have good financial flexibility.'
            elif dti_percentage <= 36:
                status = 'good'
                recommendation = 'Good debt-to-income ratio. You should be able to manage additional debt responsibly.'
            elif dti_percentage <= 43:
                status = 'fair'
                recommendation = 'Fair debt-to-income ratio. Consider reducing debt before taking on new obligations.'
            else:
                status = 'poor'
                recommendation = 'High debt-to-income ratio. Focus on debt reduction and avoid new debt.'
            
            return {
                'monthly_debt_payments': monthly_debt_payments,
                'monthly_income': monthly_income,
                'dti_ratio': dti_ratio,
                'dti_percentage': dti_percentage,
                'status': status,
                'recommendation': recommendation,
            }
            
        except Exception as e:
            logger.error(f"Error calculating debt-to-income ratio: {e}")
            return {
                'monthly_debt_payments': 0,
                'monthly_income': 0,
                'dti_ratio': 0,
                'dti_percentage': 0,
                'status': 'error',
                'recommendation': 'Error calculating debt-to-income ratio.',
            }

    @staticmethod
    def calculate_net_worth(assets, liabilities):
        """
        Calculate net worth.
        
        Args:
            assets: Total assets value
            liabilities: Total liabilities value
        
        Returns:
            Dictionary with net worth calculation details
        """
        try:
            assets = float(assets)
            liabilities = float(liabilities)
            
            net_worth = assets - liabilities
            
            # Determine financial health status
            if net_worth > 0:
                status = 'positive'
                recommendation = 'Positive net worth. You have more assets than liabilities.'
            elif net_worth == 0:
                status = 'neutral'
                recommendation = 'Neutral net worth. Your assets equal your liabilities.'
            else:
                status = 'negative'
                recommendation = 'Negative net worth. Focus on reducing liabilities and increasing assets.'
            
            return {
                'assets': assets,
                'liabilities': liabilities,
                'net_worth': net_worth,
                'status': status,
                'recommendation': recommendation,
            }
            
        except Exception as e:
            logger.error(f"Error calculating net worth: {e}")
            return {
                'assets': 0,
                'liabilities': 0,
                'net_worth': 0,
                'status': 'error',
                'recommendation': 'Error calculating net worth.',
            }

    @staticmethod
    def format_currency(amount, currency="KES", locale="en_KE"):
        """
        Format amount as currency string.
        
        Args:
            amount: Amount to format
            currency: Currency code (KES, USD, EUR, etc.)
            locale: Locale for formatting
        
        Returns:
            Formatted currency string
        """
        try:
            amount = float(amount)
            
            # Currency symbols and formatting
            currency_info = {
                'KES': {'symbol': 'KSh', 'decimal_places': 2},
                'USD': {'symbol': '$', 'decimal_places': 2},
                'EUR': {'symbol': '€', 'decimal_places': 2},
                'GBP': {'symbol': '£', 'decimal_places': 2},
            }
            
            info = currency_info.get(currency, {'symbol': currency, 'decimal_places': 2})
            symbol = info['symbol']
            decimal_places = info['decimal_places']
            
            # Format with commas for thousands
            formatted_amount = f"{amount:,.{decimal_places}f}"
            
            # Add currency symbol
            if currency == 'USD':
                return f"{symbol}{formatted_amount}"
            else:
                return f"{formatted_amount} {symbol}"
                
        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return f"{amount} {currency}"

    @staticmethod
    def validate_financial_data(data, required_fields=None):
        """
        Validate financial data for completeness and correctness.
        
        Args:
            data: Dictionary containing financial data
            required_fields: List of required field names
        
        Returns:
            Dictionary with validation results
        """
        try:
            if required_fields is None:
                required_fields = ['amount', 'currency']
            
            errors = []
            warnings = []
            
            # Check required fields
            for field in required_fields:
                if field not in data or data[field] is None or data[field] == '':
                    errors.append(f"Required field '{field}' is missing or empty.")
            
            # Validate amount if present
            if 'amount' in data:
                try:
                    amount = float(data['amount'])
                    if amount < 0:
                        warnings.append("Amount is negative.")
                    if amount == 0:
                        warnings.append("Amount is zero.")
                except (ValueError, TypeError):
                    errors.append("Amount must be a valid number.")
            
            # Validate currency if present
            if 'currency' in data:
                valid_currencies = ['KES', 'USD', 'EUR', 'GBP']
                if data['currency'] not in valid_currencies:
                    warnings.append(f"Currency '{data['currency']}' may not be supported.")
            
            # Validate date if present
            if 'date' in data:
                try:
                    from datetime import datetime
                    datetime.strptime(data['date'], '%Y-%m-%d')
                except ValueError:
                    errors.append("Date must be in YYYY-MM-DD format.")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'data': data,
            }
            
        except Exception as e:
            logger.error(f"Error validating financial data: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'data': data,
            }


