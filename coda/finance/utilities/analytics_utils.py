"""
Analytics Utilities

This module contains utility functions for financial analytics including
reporting, data analysis, and performance metrics.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, Count, Avg
from decimal import Decimal
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import logging
import requests
from mail.custom_email import send_email

logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()


class AnalyticsUtils:
    """Utility class for financial analytics operations."""
    
    @staticmethod
    def calculate_portfolio_performance(portfolio_data, time_period_months=12):
        """
        Calculate portfolio performance metrics.
        
        Args:
            portfolio_data: List of portfolio values over time
            time_period_months: Time period for analysis in months
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            if not portfolio_data or len(portfolio_data) < 2:
                return {
                    'total_return': 0,
                    'total_return_percentage': 0,
                    'annualized_return': 0,
                    'volatility': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'data_points': 0,
                }
            
            # Calculate returns
            returns = []
            for i in range(1, len(portfolio_data)):
                if portfolio_data[i-1] > 0:
                    return_rate = (portfolio_data[i] - portfolio_data[i-1]) / portfolio_data[i-1]
                    returns.append(return_rate)
            
            if not returns:
                return {
                    'total_return': 0,
                    'total_return_percentage': 0,
                    'annualized_return': 0,
                    'volatility': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'data_points': len(portfolio_data),
                }
            
            # Total return
            initial_value = portfolio_data[0]
            final_value = portfolio_data[-1]
            total_return = final_value - initial_value
            total_return_percentage = (total_return / initial_value) * 100 if initial_value > 0 else 0
            
            # Annualized return
            time_years = time_period_months / 12
            annualized_return = ((final_value / initial_value) ** (1 / time_years)) - 1 if time_years > 0 and initial_value > 0 else 0
            
            # Volatility (standard deviation of returns)
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5
            
            # Sharpe ratio (assuming risk-free rate of 2%)
            risk_free_rate = 0.02
            sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # Maximum drawdown
            peak = initial_value
            max_drawdown = 0
            for value in portfolio_data:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'total_return': total_return,
                'total_return_percentage': total_return_percentage,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'data_points': len(portfolio_data),
                'initial_value': initial_value,
                'final_value': final_value,
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio performance: {e}")
            return {
                'total_return': 0,
                'total_return_percentage': 0,
                'annualized_return': 0,
                'volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'data_points': 0,
            }

    @staticmethod
    def calculate_loan_performance_metrics(loan_data):
        """
        Calculate loan performance metrics.
        
        Args:
            loan_data: List of loan records with payment information
        
        Returns:
            Dictionary with loan performance metrics
        """
        try:
            if not loan_data:
                return {
                    'total_loans': 0,
                    'total_amount': 0,
                    'total_paid': 0,
                    'total_outstanding': 0,
                    'default_rate': 0,
                    'average_loan_size': 0,
                    'collection_rate': 0,
                }
            
            total_loans = len(loan_data)
            total_amount = sum(loan.get('amount', 0) for loan in loan_data)
            total_paid = sum(loan.get('paid_amount', 0) for loan in loan_data)
            total_outstanding = total_amount - total_paid
            
            # Default rate calculation
            defaulted_loans = sum(1 for loan in loan_data if loan.get('status') == 'defaulted')
            default_rate = (defaulted_loans / total_loans) * 100 if total_loans > 0 else 0
            
            # Average loan size
            average_loan_size = total_amount / total_loans if total_loans > 0 else 0
            
            # Collection rate
            collection_rate = (total_paid / total_amount) * 100 if total_amount > 0 else 0
            
            return {
                'total_loans': total_loans,
                'total_amount': total_amount,
                'total_paid': total_paid,
                'total_outstanding': total_outstanding,
                'default_rate': default_rate,
                'average_loan_size': average_loan_size,
                'collection_rate': collection_rate,
                'defaulted_loans': defaulted_loans,
            }
            
        except Exception as e:
            logger.error(f"Error calculating loan performance metrics: {e}")
            return {
                'total_loans': 0,
                'total_amount': 0,
                'total_paid': 0,
                'total_outstanding': 0,
                'default_rate': 0,
                'average_loan_size': 0,
                'collection_rate': 0,
            }

    @staticmethod
    def generate_financial_summary(user_data, time_period_months=12):
        """
        Generate comprehensive financial summary for a user.
        
        Args:
            user_data: Dictionary containing user's financial data
            time_period_months: Time period for analysis
        
        Returns:
            Dictionary with financial summary
        """
        try:
            # Extract data
            income_data = user_data.get('income', [])
            expense_data = user_data.get('expenses', [])
            loan_data = user_data.get('loans', [])
            investment_data = user_data.get('investments', [])
            
            # Calculate income metrics
            total_income = sum(item.get('amount', 0) for item in income_data)
            average_monthly_income = total_income / time_period_months if time_period_months > 0 else 0
            
            # Calculate expense metrics
            total_expenses = sum(item.get('amount', 0) for item in expense_data)
            average_monthly_expenses = total_expenses / time_period_months if time_period_months > 0 else 0
            
            # Calculate loan metrics
            total_loan_amount = sum(loan.get('amount', 0) for loan in loan_data)
            total_loan_payments = sum(loan.get('monthly_payment', 0) for loan in loan_data)
            
            # Calculate investment metrics
            total_investment_value = sum(investment.get('current_value', 0) for investment in investment_data)
            total_investment_cost = sum(investment.get('cost', 0) for investment in investment_data)
            investment_gain_loss = total_investment_value - total_investment_cost
            
            # Calculate net worth
            assets = total_investment_value
            liabilities = total_loan_amount
            net_worth = assets - liabilities
            
            # Calculate savings rate
            net_income = total_income - total_expenses
            savings_rate = (net_income / total_income) * 100 if total_income > 0 else 0
            
            # Calculate debt-to-income ratio
            dti_ratio = (total_loan_payments / average_monthly_income) * 100 if average_monthly_income > 0 else 0
            
            return {
                'time_period_months': time_period_months,
                'income': {
                    'total': total_income,
                    'monthly_average': average_monthly_income,
                    'transactions': len(income_data),
                },
                'expenses': {
                    'total': total_expenses,
                    'monthly_average': average_monthly_expenses,
                    'transactions': len(expense_data),
                },
                'loans': {
                    'total_amount': total_loan_amount,
                    'monthly_payments': total_loan_payments,
                    'count': len(loan_data),
                },
                'investments': {
                    'total_value': total_investment_value,
                    'total_cost': total_investment_cost,
                    'gain_loss': investment_gain_loss,
                    'count': len(investment_data),
                },
                'net_worth': net_worth,
                'savings_rate': savings_rate,
                'debt_to_income_ratio': dti_ratio,
                'financial_health_score': AnalyticsUtils._calculate_financial_health_score(
                    savings_rate, dti_ratio, net_worth
                ),
            }
            
        except Exception as e:
            logger.error(f"Error generating financial summary: {e}")
            return {
                'time_period_months': time_period_months,
                'income': {'total': 0, 'monthly_average': 0, 'transactions': 0},
                'expenses': {'total': 0, 'monthly_average': 0, 'transactions': 0},
                'loans': {'total_amount': 0, 'monthly_payments': 0, 'count': 0},
                'investments': {'total_value': 0, 'total_cost': 0, 'gain_loss': 0, 'count': 0},
                'net_worth': 0,
                'savings_rate': 0,
                'debt_to_income_ratio': 0,
                'financial_health_score': 0,
            }

    @staticmethod
    def _calculate_financial_health_score(savings_rate, dti_ratio, net_worth):
        """
        Calculate overall financial health score.
        
        Args:
            savings_rate: Savings rate percentage
            dti_ratio: Debt-to-income ratio percentage
            net_worth: Net worth amount
        
        Returns:
            Financial health score (0-100)
        """
        try:
            score = 0
            
            # Savings rate component (0-40 points)
            if savings_rate >= 20:
                score += 40
            elif savings_rate >= 15:
                score += 30
            elif savings_rate >= 10:
                score += 20
            elif savings_rate >= 5:
                score += 10
            
            # Debt-to-income ratio component (0-30 points)
            if dti_ratio <= 20:
                score += 30
            elif dti_ratio <= 36:
                score += 20
            elif dti_ratio <= 43:
                score += 10
            
            # Net worth component (0-30 points)
            if net_worth > 0:
                score += 30
            elif net_worth == 0:
                score += 15
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating financial health score: {e}")
            return 0

    @staticmethod
    def generate_trend_analysis(data, time_period_months=12):
        """
        Generate trend analysis for financial data.
        
        Args:
            data: List of data points over time
            time_period_months: Time period for analysis
        
        Returns:
            Dictionary with trend analysis
        """
        try:
            if not data or len(data) < 2:
                return {
                    'trend': 'insufficient_data',
                    'slope': 0,
                    'correlation': 0,
                    'volatility': 0,
                    'prediction': 0,
                }
            
            # Calculate trend slope
            n = len(data)
            x_values = list(range(n))
            y_values = data
            
            # Simple linear regression
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
            
            # Calculate correlation
            mean_x = sum_x / n
            mean_y = sum_y / n
            
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
            denominator_x = sum((x - mean_x) ** 2 for x in x_values)
            denominator_y = sum((y - mean_y) ** 2 for y in y_values)
            
            correlation = numerator / ((denominator_x * denominator_y) ** 0.5) if (denominator_x * denominator_y) > 0 else 0
            
            # Calculate volatility
            returns = [(y_values[i] - y_values[i-1]) / y_values[i-1] for i in range(1, len(y_values)) if y_values[i-1] != 0]
            volatility = (sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns))**0.5 if returns else 0
            
            # Determine trend direction
            if slope > 0.01:
                trend = 'increasing'
            elif slope < -0.01:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            # Simple prediction (next period)
            prediction = y_values[-1] + slope if slope != 0 else y_values[-1]
            
            return {
                'trend': trend,
                'slope': slope,
                'correlation': correlation,
                'volatility': volatility,
                'prediction': prediction,
                'data_points': n,
                'first_value': y_values[0],
                'last_value': y_values[-1],
            }
            
        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            return {
                'trend': 'error',
                'slope': 0,
                'correlation': 0,
                'volatility': 0,
                'prediction': 0,
            }

    @staticmethod
    def calculate_risk_metrics(returns_data, risk_free_rate=0.02):
        """
        Calculate risk metrics for investment analysis.
        
        Args:
            returns_data: List of return rates
            risk_free_rate: Risk-free rate (default 2%)
        
        Returns:
            Dictionary with risk metrics
        """
        try:
            if not returns_data or len(returns_data) < 2:
                return {
                    'volatility': 0,
                    'sharpe_ratio': 0,
                    'var_95': 0,
                    'var_99': 0,
                    'max_drawdown': 0,
                    'beta': 0,
                }
            
            # Calculate volatility (standard deviation)
            mean_return = sum(returns_data) / len(returns_data)
            variance = sum((r - mean_return) ** 2 for r in returns_data) / len(returns_data)
            volatility = variance ** 0.5
            
            # Calculate Sharpe ratio
            excess_return = mean_return - risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            # Calculate Value at Risk (VaR)
            sorted_returns = sorted(returns_data)
            var_95_index = int(len(sorted_returns) * 0.05)
            var_99_index = int(len(sorted_returns) * 0.01)
            
            var_95 = sorted_returns[var_95_index] if var_95_index < len(sorted_returns) else sorted_returns[0]
            var_99 = sorted_returns[var_99_index] if var_99_index < len(sorted_returns) else sorted_returns[0]
            
            # Calculate maximum drawdown
            peak = 0
            max_drawdown = 0
            cumulative_return = 0
            
            for return_rate in returns_data:
                cumulative_return += return_rate
                if cumulative_return > peak:
                    peak = cumulative_return
                drawdown = peak - cumulative_return
                max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'var_95': var_95,
                'var_99': var_99,
                'max_drawdown': max_drawdown,
                'beta': 1.0,  # Placeholder - would need market data
                'mean_return': mean_return,
                'excess_return': excess_return,
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {
                'volatility': 0,
                'sharpe_ratio': 0,
                'var_95': 0,
                'var_99': 0,
                'max_drawdown': 0,
                'beta': 0,
            }


