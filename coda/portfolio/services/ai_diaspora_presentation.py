"""
AI Diaspora Platform Presentation Service
Integrates with existing ai_services presentation logic
"""

from .base_presentation import BasePresentationService, ProjectRegistry


class AIDiasporaPresentationService(BasePresentationService):
    """Presentation service for AI Diaspora Platform"""
    
    project_name = "AI Diaspora Platform"
    project_slug = "ai-diaspora"
    project_tagline = "Transforming $50B+ African Diaspora Market Through AI"
    created_date = "2024"
    
    def get_technologies(self):
        return {
            'backend': [
                {'name': 'Django', 'use': 'Web Framework', 'icon': 'fab fa-python'},
                {'name': 'PostgreSQL', 'use': 'Database', 'icon': 'fas fa-database'},
            ],
            'ai_ml': [
                {'name': 'AI Risk Scoring', 'use': 'Investment Analysis', 'icon': 'fas fa-brain'},
                {'name': 'Predictive Analytics', 'use': 'Market Trends', 'icon': 'fas fa-chart-line'},
            ],
            'frontend': [
                {'name': 'React', 'use': 'UI Framework', 'icon': 'fab fa-react'},
                {'name': 'D3.js', 'use': 'Data Visualization', 'icon': 'fas fa-chart-bar'},
            ],
        }
    
    def get_key_metrics(self):
        return {
            'market_size': '$50B+',
            'diaspora_population': '200M+',
            'annual_growth': '15%',
            'ai_accuracy': '90%+',
        }
    
    def get_investor_context(self):
        return {
            'subtitle': 'Transforming $50B+ African Diaspora Market Through AI-Driven Financial Services',
            'market_opportunity': {
                'problem': 'African diaspora faces high remittance costs and limited investment opportunities',
                'solution': 'AI-powered platform connecting diaspora with investment and financial services',
                'market_size': '$50B+ annual remittances',
                'growth_rate': '15% annual growth',
            },
        }
    
    def get_technical_context(self):
        return {
            'subtitle': 'AI-Powered Risk Analysis & Real-Time Analytics',
            'technical_highlights': [
                {
                    'category': 'AI/ML Implementation',
                    'icon': 'fas fa-brain',
                    'skills': [
                        'AI risk scoring algorithms',
                        'Predictive analytics for market trends',
                        'Real-time data processing',
                    ],
                },
            ],
        }


# Register this service
ProjectRegistry.register('ai-diaspora', AIDiasporaPresentationService)

