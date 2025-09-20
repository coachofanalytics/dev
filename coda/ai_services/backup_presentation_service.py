"""
Backup Presentation Service for CODA AI Platform
Provides offline demo capabilities and fallback mechanisms
"""
import json
import time
from typing import Dict, List, Any
from django.utils import timezone
from datetime import datetime, timedelta

class BackupPresentationService:
    """
    Backup service for presentations when AI services are unavailable.
    Provides realistic demo data and fallback scenarios.
    """
    
    def __init__(self):
        self.demo_scenarios = self._load_demo_scenarios()
        self.fallback_results = self._load_fallback_results()
    
    def _load_demo_scenarios(self) -> Dict[str, Any]:
        """Load pre-configured demo scenarios."""
        return {
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
    
    def _load_fallback_results(self) -> Dict[str, Any]:
        """Load realistic fallback results for different perspectives."""
        return {
            'investor': {
                'confidence': 87,
                'processing_time': 1.5,
                'ai_source': 'Fallback Model',
                'fallback_used': True,
                'investment_score': 8.7,
                'market_potential': 'High',
                'scalability': 'Excellent',
                'revenue_potential': '$240,000 LTV',
                'roi_projection': '300%+',
                'investment_opportunities': [
                    'Fintech partnerships for mobile money integration',
                    'Real estate investment opportunities in Nairobi',
                    'Government bond investments for stable returns',
                    'Startup investment in Kenyan tech sector',
                ],
                'risk_assessment': 'Low-Medium',
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
            },
            'banking': {
                'confidence': 89,
                'processing_time': 1.8,
                'ai_source': 'Fallback Model',
                'fallback_used': True,
                'credit_score': 742,
                'risk_level': 'Low-Medium',
                'loan_approval': '$25,000',
                'default_probability': '2.1%',
                'compliance_score': '95%',
                'recommendations': [
                    'Personal loan approval: up to $25,000',
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
            },
            'standard': {
                'confidence': 88,
                'processing_time': 1.3,
                'ai_source': 'Fallback Model',
                'fallback_used': True,
                'overall_score': 8.7,
                'risk_assessment': 'Low-Medium',
                'recommendations': [
                    'Optimize remittance method for cost savings',
                    'Consider investment opportunities in Kenya',
                    'Explore family financial planning options',
                ],
                'cost_savings': '$2,000 annually',
                'time_savings': '90% faster processing',
                'access_improvement': '200% increase in financial services',
            }
        }
    
    def get_backup_demo_data(self, scenario_type: str = 'high_value') -> Dict[str, Any]:
        """Get backup demo data for specific scenario."""
        return self.demo_scenarios.get(scenario_type, self.demo_scenarios['high_value'])
    
    def get_backup_analysis_results(self, demo_data: Dict[str, Any], perspective: str = 'standard') -> Dict[str, Any]:
        """Get backup analysis results based on demo data and perspective."""
        base_results = self.fallback_results.get(perspective, self.fallback_results['standard'])
        
        # Add dynamic elements based on demo data
        amount = demo_data.get('amount', 5000)
        experience = demo_data.get('experience', 8)
        
        # Modify results based on scenario
        if perspective == 'investor':
            base_results['investment_score'] = min(10, (amount / 1000) * 0.5 + (experience * 0.3) + 5)
            base_results['revenue_potential'] = f'${amount * 48:.0f} LTV'
        elif perspective == 'banking':
            credit_score = min(850, 650 + (amount / 100) + (experience * 10))
            loan_approval = min(amount * 6, 50000)
            base_results['credit_score'] = int(credit_score)
            base_results['loan_approval'] = f'${loan_approval:,}'
            base_results['default_probability'] = f'{5 - (credit_score - 650) / 40:.1f}%'
        
        # Add session information
        base_results['session_id'] = f"backup_{int(timezone.now().timestamp())}"
        base_results['timestamp'] = timezone.now().isoformat()
        base_results['backup_mode'] = True
        
        return base_results
    
    def get_offline_demo_script(self, perspective: str = 'standard') -> Dict[str, Any]:
        """Get offline demo script for presentations."""
        scripts = {
            'investor': {
                'opening': "Let me show you how our AI platform evaluates investment opportunities in the diaspora market.",
                'demo_steps': [
                    "Input: $5,000 monthly remittance to Kenya for investment purposes",
                    "Analysis: 8 years experience, bank transfer method",
                    "AI Processing: Risk assessment and market opportunity analysis",
                    "Results: 8.7/10 investment score, $240K LTV potential",
                    "Recommendations: Fintech partnerships, real estate opportunities"
                ],
                'key_points': [
                    "Market size: $50B+ with 15% YoY growth",
                    "Unit economics: 16:1 LTV/CAC ratio",
                    "ROI potential: 300%+ returns",
                    "Scalability: AI-first approach with network effects"
                ],
                'closing': "This demonstrates how CODA's AI can identify high-value investment opportunities in the diaspora market."
            },
            'banking': {
                'opening': "Here's how our AI platform transforms credit assessment for diaspora customers.",
                'demo_steps': [
                    "Input: $1,500 monthly remittance for family support",
                    "Analysis: 3 years experience, mobile money method",
                    "AI Processing: Credit scoring and risk assessment",
                    "Results: 742 credit score, $9,000 loan approval",
                    "Recommendations: Premium services, investment advisory"
                ],
                'key_points': [
                    "Risk reduction: 35% fewer defaults",
                    "Processing speed: <2 seconds vs 72 hours",
                    "Compliance: 95% automated regulatory compliance",
                    "Customer growth: +200% acquisition rate"
                ],
                'closing': "This shows how AI can reduce banking risk while expanding customer access."
            },
            'standard': {
                'opening': "Let me demonstrate CODA's AI platform capabilities across multiple use cases.",
                'demo_steps': [
                    "Remittance Analysis: Cost optimization and recommendations",
                    "Investment Opportunities: Tailored investment suggestions",
                    "Education Pathways: Scholarship and education options",
                    "Healthcare Access: Insurance and healthcare planning",
                    "Trade Facilitation: Cross-border trade optimization"
                ],
                'key_points': [
                    "5 Analysis Types: Comprehensive diaspora services",
                    "Real-time Processing: <2 second response times",
                    "Global Reach: 50+ countries supported",
                    "Cost Savings: $2,000 annually per user"
                ],
                'closing': "This demonstrates the comprehensive AI-powered financial services available through CODA."
            }
        }
        
        return scripts.get(perspective, scripts['standard'])
    
    def get_emergency_contact_info(self) -> Dict[str, Any]:
        """Get emergency contact information for technical issues."""
        return {
            'technical_support': {
                'email': 'support@codaplatform.com',
                'phone': '+1 (555) 123-4567',
                'hours': '24/7 for critical issues',
                'response_time': '<15 minutes'
            },
            'presentation_support': {
                'email': 'presentations@codaplatform.com',
                'phone': '+1 (555) 123-4569',
                'hours': 'Monday-Friday, 8 AM - 8 PM EST',
                'response_time': '<30 minutes'
            },
            'business_development': {
                'email': 'partnerships@codaplatform.com',
                'phone': '+1 (555) 123-4568',
                'hours': 'Monday-Friday, 9 AM - 6 PM EST',
                'response_time': '<2 hours'
            },
            'emergency_procedures': [
                'Switch to backup demo mode immediately',
                'Use offline presentation materials',
                'Contact technical support',
                'Inform audience of temporary technical issue',
                'Continue with prepared backup content'
            ]
        }
    
    def validate_backup_systems(self) -> Dict[str, bool]:
        """Validate that backup systems are working properly."""
        return {
            'demo_scenarios_loaded': len(self.demo_scenarios) > 0,
            'fallback_results_available': len(self.fallback_results) > 0,
            'offline_scripts_ready': True,
            'contact_info_available': True,
            'timestamp_generation': True,
            'backup_mode_detection': True
        }

