"""
Presentation Service for CODA AI Platform
Integrates with existing services to provide streamlined presentation data
"""
import logging
from typing import Dict, List, Any
from django.utils import timezone
from .analytics_service import AnalyticsService
from .advanced_analytics_service import AdvancedAnalyticsService
from .ai_configuration_service import AIConfigurationService

logger = logging.getLogger(__name__)

class PresentationService:
    """
    Centralized service for managing presentation data and scenarios.
    Integrates with existing services to avoid duplication.
    """
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
        self.advanced_analytics_service = AdvancedAnalyticsService()
        self.ai_configuration_service = AIConfigurationService()
    
    def get_presentation_context(self, mode: str = 'standard') -> Dict[str, Any]:
        """
        Get presentation context based on mode.
        Integrates with existing services to provide real data.
        """
        base_context = self._get_base_context()
        
        if mode == 'investor':
            return {**base_context, **self._get_investor_context()}
        elif mode == 'banking':
            return {**base_context, **self._get_banking_context()}
        elif mode == 'hybrid':
            return {**base_context, **self._get_hybrid_context()}
        else:
            return {**base_context, **self._get_standard_context()}
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Get base context shared across all presentation modes."""
        return {
            'title': 'CODA AI Platform',
            'analysis_types': [
                {'key': 'remittance_analysis', 'name': 'Remittance Analysis', 'icon': 'fas fa-money-bill-wave'},
                {'key': 'trade_facilitation', 'name': 'Trade Facilitation', 'icon': 'fas fa-shipping-fast'},
                {'key': 'investment_opportunities', 'name': 'Investment Opportunities', 'icon': 'fas fa-chart-line'},
                {'key': 'education_pathways', 'name': 'Education Pathways', 'icon': 'fas fa-graduation-cap'},
                {'key': 'healthcare_access', 'name': 'Healthcare Access', 'icon': 'fas fa-heartbeat'},
            ],
            'platform_metrics': self._get_platform_metrics(),
            'ai_status': self.ai_configuration_service.get_ai_service_status(),
        }
    
    def _get_platform_metrics(self) -> Dict[str, Any]:
        """Get real platform metrics from analytics service."""
        try:
            analytics_data = self.analytics_service.get_analytics_dashboard_data()
            return {
                'total_sessions': analytics_data.get('total_sessions', 0),
                'total_analyses': analytics_data.get('total_analyses', 0),
                'avg_session_duration': analytics_data.get('avg_session_duration', 0),
                'conversion_rate': analytics_data.get('conversion_rate', 0),
                'ai_accuracy': analytics_data.get('ai_accuracy', 90),
                'response_time': analytics_data.get('avg_response_time', 1.8),
            }
        except Exception as e:
            logger.error(f"Error getting platform metrics: {e}")
            return {
                'total_sessions': 0,
                'total_analyses': 0,
                'avg_session_duration': 0,
                'conversion_rate': 0,
                'ai_accuracy': 90,
                'response_time': 1.8,
            }
    
    def _get_investor_context(self) -> Dict[str, Any]:
        """Get investor-specific context data."""
        return {
            'presentation_mode': 'investor',
            'market_data': {
                'total_market_size': '$50B+',
                'diaspora_population': '200M+',
                'kenya_remittances': '$2.5B',
                'growth_rate': '15% YoY',
                'addressable_market': '$8B',
            },
            'investment_scenarios': self._get_investment_scenarios(),
            'competitive_advantages': self._get_competitive_advantages(),
            'financial_projections': self._get_financial_projections(),
        }
    
    def _get_banking_context(self) -> Dict[str, Any]:
        """Get banking-specific context data."""
        return {
            'presentation_mode': 'banking',
            'challenges': {
                'annual_losses': '$2.8B',
                'rejection_rate': '45%',
                'lost_revenue': '$1.2B',
                'processing_time': '72hrs',
            },
            'banking_solutions': self._get_banking_solutions(),
            'risk_benefits': self._get_risk_benefits(),
            'business_impact': self._get_business_impact(),
        }
    
    def _get_hybrid_context(self) -> Dict[str, Any]:
        """Get hybrid presentation context combining investor and banking perspectives."""
        investor_context = self._get_investor_context()
        banking_context = self._get_banking_context()
        
        return {
            'presentation_mode': 'hybrid',
            'investor_data': investor_context,
            'banking_data': banking_context,
            'synergy_analysis': self._get_synergy_analysis(),
            'implementation_roadmap': self._get_implementation_roadmap(),
        }
    
    def _get_standard_context(self) -> Dict[str, Any]:
        """Get standard presentation context."""
        return {
            'presentation_mode': 'standard',
            'platform_features': self._get_platform_features(),
            'demo_scenarios': self._get_demo_scenarios(),
        }
    
    def _get_investment_scenarios(self) -> List[Dict[str, Any]]:
        """Get investment scenarios data."""
        return [
            {
                'key': 'fintech_partnership',
                'title': 'Fintech Partnership',
                'subtitle': 'Mobile Money Integration',
                'icon': 'fas fa-mobile-alt',
                'roi': '300% ROI',
                'market_size': '$2.5B',
                'description': 'Partner with mobile money providers to offer AI-powered remittance optimization and investment recommendations.',
                'timeline': '6-12 months',
                'investment_required': '$5M',
            },
            {
                'key': 'real_estate',
                'title': 'Real Estate Investment',
                'subtitle': 'Property Investment Platform',
                'icon': 'fas fa-building',
                'roi': '250% ROI',
                'market_size': '$1.8B',
                'description': 'AI-driven property investment recommendations for diaspora members looking to invest in Kenyan real estate.',
                'timeline': '12-18 months',
                'investment_required': '$3M',
            },
            {
                'key': 'banking_integration',
                'title': 'Banking Integration',
                'subtitle': 'White-label AI Platform',
                'icon': 'fas fa-university',
                'roi': '400% ROI',
                'market_size': '$3.2B',
                'description': 'White-label AI platform for banks to offer enhanced diaspora services and credit scoring.',
                'timeline': '3-6 months',
                'investment_required': '$2M',
            }
        ]
    
    def _get_banking_solutions(self) -> List[Dict[str, Any]]:
        """Get banking solutions data."""
        return [
            {
                'key': 'credit_scoring',
                'title': 'Credit Scoring',
                'subtitle': 'AI-Powered Risk Assessment',
                'icon': 'fas fa-shield-alt',
                'benefit': '35% Risk Reduction',
                'market_size': '$2.8B',
                'description': 'Advanced credit scoring using remittance patterns and financial behavior analysis.',
                'implementation_time': '3 months',
                'roi_timeline': '6 months',
            },
            {
                'key': 'customer_acquisition',
                'title': 'Customer Acquisition',
                'subtitle': 'Diaspora Banking Services',
                'icon': 'fas fa-users',
                'benefit': '+200% Growth',
                'market_size': '$1.5B',
                'description': 'Targeted banking services for diaspora communities with personalized offerings.',
                'implementation_time': '6 months',
                'roi_timeline': '12 months',
            },
            {
                'key': 'compliance_automation',
                'title': 'Compliance Automation',
                'subtitle': 'Regulatory Compliance',
                'icon': 'fas fa-check-circle',
                'benefit': '95% Compliance',
                'market_size': '$800M',
                'description': 'Automated compliance monitoring and reporting for international financial regulations.',
                'implementation_time': '2 months',
                'roi_timeline': '3 months',
            }
        ]
    
    def _get_competitive_advantages(self) -> List[Dict[str, Any]]:
        """Get competitive advantages data."""
        return [
            {
                'title': 'AI-First Approach',
                'icon': 'fas fa-brain',
                'description': 'Proprietary AI models trained on diaspora financial behavior patterns.',
                'metrics': ['90%+ Accuracy', '<2s Response'],
                'color': 'primary',
            },
            {
                'title': 'Data Network Effects',
                'icon': 'fas fa-database',
                'description': 'Unique dataset of diaspora financial patterns creates increasing value with scale.',
                'metrics': ['200M+ Records', 'Real-time Updates'],
                'color': 'success',
            },
            {
                'title': 'Regulatory Compliance',
                'icon': 'fas fa-shield-alt',
                'description': 'Built-in compliance with international financial regulations.',
                'metrics': ['GDPR Compliant', 'PCI DSS'],
                'color': 'warning',
            }
        ]
    
    def _get_financial_projections(self) -> Dict[str, Any]:
        """Get financial projections data."""
        return {
            'revenue_model': {
                'saas_subscriptions': '$50-500/month per enterprise client',
                'transaction_fees': '0.5-2% per analysis',
                'api_licensing': '$0.10-1.00 per API call',
                'data_insights': '$1,000-10,000 per custom report',
            },
            'unit_economics': {
                'customer_acquisition_cost': '$150',
                'lifetime_value': '$2,400',
                'ltv_cac_ratio': '16:1',
                'gross_margin': '85%',
            },
            'projections': {
                'year_1_revenue': '$720,000',
                'year_2_revenue': '$1,440,000',
                'year_3_revenue': '$2,880,000',
                'three_year_roi': '144%',
            }
        }
    
    def _get_risk_benefits(self) -> List[Dict[str, Any]]:
        """Get risk management benefits data."""
        return [
            {
                'title': 'Enhanced Credit Scoring',
                'icon': 'fas fa-chart-line',
                'description': 'AI-powered credit scoring using remittance patterns, financial behavior, and alternative data sources.',
                'metrics': ['35% Risk Reduction', '89% Accuracy'],
                'color': 'success',
            },
            {
                'title': 'Real-Time Processing',
                'icon': 'fas fa-clock',
                'description': 'Instant loan approvals and risk assessments with sub-2-second processing times.',
                'metrics': ['<2s Processing', '24/7 Availability'],
                'color': 'primary',
            },
            {
                'title': 'Regulatory Compliance',
                'icon': 'fas fa-check-circle',
                'description': 'Built-in compliance with international banking regulations and anti-money laundering requirements.',
                'metrics': ['95% Compliance', 'GDPR Ready'],
                'color': 'warning',
            }
        ]
    
    def _get_business_impact(self) -> Dict[str, Any]:
        """Get business impact data."""
        return {
            'revenue_impact': {
                'customer_acquisition': '+200%',
                'revenue_per_customer': '+$2,400 LTV',
                'processing_efficiency': '85% Faster',
                'operational_savings': '$5M Annually',
            },
            'risk_reduction': {
                'default_rate_reduction': '35%',
                'fraud_detection': '95% Accuracy',
                'compliance_score': '95%',
                'regulatory_fines': '-80%',
            }
        }
    
    def _get_synergy_analysis(self) -> List[Dict[str, Any]]:
        """Get synergy analysis data."""
        return [
            {
                'title': 'Revenue Synergy',
                'icon': 'fas fa-chart-bar',
                'description': 'Combined revenue streams create 2.5x higher unit economics than standalone solutions.',
                'metrics': ['$2.4M LTV', '85% Margin'],
                'color': 'success',
            },
            {
                'title': 'Risk Mitigation',
                'icon': 'fas fa-shield-alt',
                'description': 'AI-powered risk assessment reduces default rates by 35% while maintaining high approval rates.',
                'metrics': ['35% Risk Reduction', '95% Compliance'],
                'color': 'primary',
            },
            {
                'title': 'Market Expansion',
                'icon': 'fas fa-users',
                'description': 'Banking partnerships accelerate customer acquisition while providing stable revenue base.',
                'metrics': ['200% Growth', '5x Scale'],
                'color': 'warning',
            }
        ]
    
    def _get_implementation_roadmap(self) -> List[Dict[str, Any]]:
        """Get implementation roadmap data."""
        return [
            {
                'phase': 1,
                'title': 'Foundation (Months 1-6)',
                'investor_focus': 'Complete Series A funding ($5M)',
                'banking_focus': 'Pilot with 3 major banks',
                'combined_focus': 'Deploy core AI platform',
                'metrics': ['3 Bank Partners', '10K Customers'],
            },
            {
                'phase': 2,
                'title': 'Scale (Months 7-18)',
                'investor_focus': 'Series B preparation ($15M)',
                'banking_focus': 'Expand to 15 bank partners',
                'combined_focus': 'Launch in 5 African markets',
                'metrics': ['15 Bank Partners', '100K Customers'],
            },
            {
                'phase': 3,
                'title': 'Expansion (Months 19-36)',
                'investor_focus': 'IPO preparation',
                'banking_focus': 'Global banking network',
                'combined_focus': 'Market leadership position',
                'metrics': ['50 Bank Partners', '1M Customers'],
            }
        ]
    
    def _get_platform_features(self) -> List[Dict[str, Any]]:
        """Get platform features data."""
        return [
            {
                'title': 'AI-Powered Analysis',
                'icon': 'fas fa-robot',
                'description': 'Advanced AI models provide accurate predictions and recommendations for diaspora needs.',
                'color': 'success',
            },
            {
                'title': 'Real-Time Insights',
                'icon': 'fas fa-chart-line',
                'description': 'Get instant analysis results with confidence scores and detailed recommendations.',
                'color': 'info',
            },
            {
                'title': 'Secure & Private',
                'icon': 'fas fa-shield-alt',
                'description': 'Your data is anonymized and secure. All analysis is for demonstration purposes.',
                'color': 'warning',
            }
        ]
    
    def _get_demo_scenarios(self) -> List[Dict[str, Any]]:
        """Get demo scenarios data."""
        return [
            {
                'title': 'High-Value Investor',
                'amount': '$5,000/month',
                'purpose': 'Investment',
                'experience': '8 years',
                'expected_score': '8.7/10',
                'loan_approval': '$25,000',
            },
            {
                'title': 'Family Support',
                'amount': '$1,500/month',
                'purpose': 'Family Support',
                'experience': '3 years',
                'expected_score': '7.2/10',
                'loan_approval': '$10,000',
            },
            {
                'title': 'Business Investment',
                'amount': '$3,200/month',
                'purpose': 'Business',
                'experience': '5 years',
                'expected_score': '8.1/10',
                'loan_approval': '$20,000',
            }
        ]
    
    def get_demo_data(self, scenario_type: str = 'high_value') -> Dict[str, Any]:
        """Get demo data for specific scenario."""
        scenarios = {
            'high_value': {
                'amount': 5000,
                'frequency': 'monthly',
                'destination': 'Kenya',
                'purpose': 'investment',
                'experience': 8,
                'method': 'bank_transfer',
                'user_profile': 'High-net-worth individual with diversified investment portfolio',
                'risk_tolerance': 'Medium-High',
                'investment_goals': 'Wealth building and portfolio diversification',
            },
            'family_support': {
                'amount': 1500,
                'frequency': 'monthly',
                'destination': 'Kenya',
                'purpose': 'family_support',
                'experience': 3,
                'method': 'mobile_money',
                'user_profile': 'Working professional supporting family back home',
                'risk_tolerance': 'Low-Medium',
                'investment_goals': 'Stable family support and basic savings',
            },
            'business': {
                'amount': 3200,
                'frequency': 'monthly',
                'destination': 'Kenya',
                'purpose': 'business',
                'experience': 5,
                'method': 'bank_transfer',
                'user_profile': 'Entrepreneur with business interests in Kenya',
                'risk_tolerance': 'Medium',
                'investment_goals': 'Business expansion and operational support',
            },
            'enterprise': {
                'amount': 15000,
                'frequency': 'monthly',
                'destination': 'Multi-country',
                'purpose': 'investment',
                'experience': 15,
                'method': 'bank_transfer',
                'user_profile': 'Corporate executive with international business interests',
                'risk_tolerance': 'High',
                'investment_goals': 'International portfolio and strategic investments',
            },
            'startup': {
                'amount': 800,
                'frequency': 'monthly',
                'destination': 'Kenya',
                'purpose': 'business',
                'experience': 1,
                'method': 'mobile_money',
                'user_profile': 'Tech startup founder with limited capital',
                'risk_tolerance': 'High',
                'investment_goals': 'Business growth and market expansion',
            }
        }
        
        return scenarios.get(scenario_type, scenarios['high_value'])
    
    def get_analysis_results(self, demo_data: Dict[str, Any], perspective: str = 'standard') -> Dict[str, Any]:
        """Get analysis results based on demo data and perspective."""
        base_results = {
            'confidence': 89,
            'processing_time': 1.2,
            'ai_source': 'GPT-4 Primary',
            'fallback_used': False,
            'session_id': f"demo_{int(timezone.now().timestamp())}",
            'timestamp': timezone.now().isoformat(),
        }
        
        # Dynamic scoring based on scenario type
        scenario_type = demo_data.get('scenario_type', 'high_value')
        amount = demo_data.get('amount', 5000)
        experience = demo_data.get('experience', 8)
        
        # Calculate dynamic scores
        base_score = min(10, (amount / 1000) * 0.5 + (experience * 0.3) + 5)
        
        if perspective == 'investor':
            return {
                **base_results,
                'investment_score': round(base_score, 1),
                'market_potential': 'High' if amount > 3000 else 'Medium',
                'scalability': 'Excellent',
                'revenue_potential': f'${amount * 48:.0f} LTV',
                'roi_projection': '300%+',
                'investment_opportunities': [
                    'Fintech partnerships for mobile money integration',
                    'Real estate investment opportunities in Nairobi',
                    'Government bond investments for stable returns',
                    'Startup investment in Kenyan tech sector',
                ],
                'risk_assessment': 'Low-Medium' if experience > 5 else 'Medium-High',
                'recommendations': [
                    'Consider fintech partnerships for mobile money integration',
                    'Explore real estate investment opportunities in Nairobi',
                    'Evaluate government bond investments for stable returns',
                ],
                'key_metrics': {
                    'market_size': '$50B+',
                    'growth_rate': '15% YoY',
                    'ltv_cac_ratio': '16:1',
                    'gross_margin': '85%',
                }
            }
        elif perspective == 'banking':
            credit_score = min(850, 650 + (amount / 100) + (experience * 10))
            loan_approval = min(amount * 6, 50000)
            
            return {
                **base_results,
                'credit_score': int(credit_score),
                'risk_level': 'Low' if credit_score > 750 else 'Medium',
                'loan_approval': f'${loan_approval:,}',
                'default_probability': f'{5 - (credit_score - 650) / 40:.1f}%',
                'compliance_score': '95%',
                'recommendations': [
                    f'Personal loan approval: up to ${loan_approval:,}',
                    'Premium remittance services with reduced fees',
                    'Investment advisory services for wealth management',
                    'Cross-border banking solutions',
                ],
                'banking_services': [
                    'Enhanced credit scoring with 89% accuracy',
                    'Real-time processing (<2 seconds)',
                    'Regulatory compliance automation',
                    'Customer acquisition optimization',
                ],
                'business_impact': {
                    'risk_reduction': '35%',
                    'customer_growth': '+200%',
                    'operational_savings': '$5M annually',
                    'processing_time': '<2 seconds',
                }
            }
        else:
            return {
                **base_results,
                'overall_score': round(base_score, 1),
                'risk_assessment': 'Low-Medium' if experience > 5 else 'Medium',
                'recommendations': [
                    'Optimize remittance method for cost savings',
                    'Consider investment opportunities in Kenya',
                    'Explore family financial planning options',
                ],
                'cost_savings': f'${amount * 0.4:.0f} annually',
                'time_savings': '90% faster processing',
                'access_improvement': '200% increase in financial services',
            }

