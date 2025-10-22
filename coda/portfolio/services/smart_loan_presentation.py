"""
Smart Loan System Presentation Service
Migrated from finance loan_system_presentation
"""

from .base_presentation import BasePresentationService, ProjectRegistry


class SmartLoanPresentationService(BasePresentationService):
    """Presentation service for Smart Loan System"""
    
    project_name = "Smart Loan System"
    project_slug = "smart-loan"
    project_tagline = "IoT + Blockchain + AI-Powered Lending"
    created_date = "2024"
    
    def get_technologies(self):
        return {
            'backend': [
                {'name': 'Django', 'use': 'Web Framework', 'icon': 'fab fa-python'},
                {'name': 'PostgreSQL', 'use': 'Database', 'icon': 'fas fa-database'},
            ],
            'blockchain': [
                {'name': 'Smart Contracts', 'use': 'Loan Automation', 'icon': 'fas fa-file-contract'},
                {'name': 'Blockchain', 'use': 'Secure Transactions', 'icon': 'fas fa-link'},
            ],
            'iot': [
                {'name': 'IoT Sensors', 'use': 'Collateral Monitoring', 'icon': 'fas fa-broadcast-tower'},
                {'name': 'Real-time Tracking', 'use': 'Asset Monitoring', 'icon': 'fas fa-map-marker-alt'},
            ],
            'ai_ml': [
                {'name': 'AI Risk Scoring', 'use': 'Credit Assessment', 'icon': 'fas fa-brain'},
                {'name': 'Predictive Analytics', 'use': 'Default Prediction', 'icon': 'fas fa-chart-line'},
            ],
        }
    
    def get_key_metrics(self):
        return {
            'market_size': '$4.8T',
            'risk_reduction': '40%',
            'automation_rate': '85%',
            'default_prediction': '92%+ accuracy',
        }
    
    def get_investor_context(self):
        return {
            'subtitle': 'Revolutionary IoT + Blockchain + AI-Powered Lending',
            'market_opportunity': {
                'problem': 'Traditional lending has high default rates and manual collateral tracking',
                'solution': 'IoT-enabled collateral monitoring with AI risk scoring and blockchain automation',
                'market_size': '$4.8 trillion global lending market',
                'growth_rate': '18% CAGR',
            },
        }
    
    def get_technical_context(self):
        return {
            'subtitle': 'IoT Integration, Blockchain Smart Contracts & AI Risk Models',
            'technical_highlights': [
                {
                    'category': 'IoT Integration',
                    'icon': 'fas fa-broadcast-tower',
                    'skills': [
                        'Real-time IoT sensor integration',
                        'GPS tracking and geofencing',
                        'Automated collateral monitoring',
                    ],
                },
                {
                    'category': 'Blockchain & Smart Contracts',
                    'icon': 'fas fa-link',
                    'skills': [
                        'Smart contract development',
                        'Automated loan disbursement',
                        'Blockchain-based transaction security',
                    ],
                },
                {
                    'category': 'AI Risk Scoring',
                    'icon': 'fas fa-brain',
                    'skills': [
                        'Machine learning credit models',
                        'Default prediction algorithms',
                        'Real-time risk assessment',
                    ],
                },
            ],
        }


# Register this service
ProjectRegistry.register('smart-loan', SmartLoanPresentationService)

