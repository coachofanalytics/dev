"""
Budget Tier System Presentation Service
Migrated from finance.services.budget_tier_presentation_service
"""

from .base_presentation import BasePresentationService, ProjectRegistry


class BudgetTierPresentationService(BasePresentationService):
    """Presentation service for Budget Tier System"""
    
    project_name = "AI-Driven Budget Tier System"
    project_slug = "budget-tier"
    project_tagline = "Intelligent Budget Approval Automation"
    created_date = "October 2025"
    
    def get_technologies(self):
        return {
            'backend': [
                {'name': 'Django 3.2', 'use': 'Web Framework', 'icon': 'fab fa-python'},
                {'name': 'PostgreSQL', 'use': 'Database', 'icon': 'fas fa-database'},
                {'name': 'Python 3.12', 'use': 'Programming Language', 'icon': 'fab fa-python'},
            ],
            'ai_ml': [
                {'name': 'Statistical Analysis', 'use': 'Pattern Detection', 'icon': 'fas fa-chart-line'},
                {'name': 'Time Series Analysis', 'use': 'Trend Prediction', 'icon': 'fas fa-calendar-alt'},
                {'name': 'Variance Modeling', 'use': 'Anomaly Detection', 'icon': 'fas fa-exclamation-triangle'},
                {'name': 'Classification Algorithms', 'use': 'Tier Assignment', 'icon': 'fas fa-layer-group'},
            ],
            'frontend': [
                {'name': 'jQuery', 'use': 'Interactive UI', 'icon': 'fab fa-js'},
                {'name': 'Bootstrap', 'use': 'Responsive Design', 'icon': 'fab fa-bootstrap'},
                {'name': 'AJAX', 'use': 'Real-time Updates', 'icon': 'fas fa-sync'},
            ],
            'devops': [
                {'name': 'Heroku', 'use': 'Cloud Deployment', 'icon': 'fas fa-cloud'},
                {'name': 'Git', 'use': 'Version Control', 'icon': 'fab fa-git-alt'},
            ],
        }
    
    def get_key_metrics(self):
        return {
            'automation_rate': '75%',
            'time_saved': '40 hours/month',
            'cost_reduction': '$50K+/year',
            'accuracy': '95%+',
            'processing_time': '<2 seconds',
            'categories_analyzed': '50+',
            'transactions_processed': '$1.49M+',
            'test_coverage': '40 tests (100% pass)',
        }
    
    def get_investor_context(self):
        return {
            'subtitle': 'Reducing Operational Costs by $50K+ Annually Through AI-Driven Automation',
            'market_opportunity': {
                'problem': 'Manual budget approval processes cost organizations $50K+ annually in labor and delays',
                'solution': 'AI-driven tier system automates 75% of approvals, reducing costs and improving efficiency',
                'market_size': '$2.5B (Enterprise Budget Management Software Market)',
                'growth_rate': '12% CAGR',
            },
            'roi_scenarios': [
                {
                    'key': 'small_org',
                    'title': 'Small Organization',
                    'subtitle': '50-200 employees',
                    'icon': 'fas fa-building',
                    'roi': '320% in Year 1',
                    'cost_savings': '$25K/year',
                    'time_savings': '20 hours/month',
                    'payback_period': '3 months',
                    'description': 'Automate routine approvals, reduce approval bottlenecks',
                },
                {
                    'key': 'medium_org',
                    'title': 'Medium Organization',
                    'subtitle': '200-1000 employees',
                    'icon': 'fas fa-city',
                    'roi': '450% in Year 1',
                    'cost_savings': '$75K/year',
                    'time_savings': '60 hours/month',
                    'payback_period': '2 months',
                    'description': 'Multi-department automation, tier-based routing',
                },
                {
                    'key': 'enterprise',
                    'title': 'Enterprise',
                    'subtitle': '1000+ employees',
                    'icon': 'fas fa-industry',
                    'roi': '600% in Year 1',
                    'cost_savings': '$200K+/year',
                    'time_savings': '200+ hours/month',
                    'payback_period': '6 weeks',
                    'description': 'Enterprise-scale automation, compliance integration',
                },
            ],
            'competitive_advantages': [
                {
                    'title': 'Data-Driven Intelligence',
                    'description': 'Uses real transaction history to classify categories, not hardcoded rules',
                    'icon': 'fas fa-brain',
                    'metrics': ['95%+ Accuracy', 'Self-Learning'],
                },
                {
                    'title': 'Proven Track Record',
                    'description': '$1.49M in transactions analyzed, 50+ categories classified automatically',
                    'icon': 'fas fa-chart-line',
                    'metrics': ['$1.49M Processed', '50+ Categories'],
                },
                {
                    'title': 'Enterprise Ready',
                    'description': 'Built on Django/PostgreSQL, deployed on Heroku with 99.9% uptime',
                    'icon': 'fas fa-shield-alt',
                    'metrics': ['99.9% Uptime', 'SOC 2 Ready'],
                },
            ],
            'financial_projections': {
                'year_1': {'revenue': '$150K', 'costs': '$50K', 'profit': '$100K'},
                'year_2': {'revenue': '$500K', 'costs': '$150K', 'profit': '$350K'},
                'year_3': {'revenue': '$1.5M', 'costs': '$400K', 'profit': '$1.1M'},
            },
        }
    
    def get_technical_context(self):
        return {
            'subtitle': 'AI/ML Implementation, System Architecture & Engineering Excellence',
            'technical_highlights': [
                {
                    'category': 'AI/ML Implementation',
                    'icon': 'fas fa-brain',
                    'skills': [
                        'Statistical pattern recognition for spending analysis',
                        'Time series analysis for recurring transaction detection',
                        'Variance modeling for anomaly detection',
                        'Multi-criteria classification algorithm for tier assignment',
                    ],
                    'code_samples': [
                        {
                            'title': 'Tier Classification Algorithm',
                            'language': 'Python',
                            'description': 'Analyzes transaction patterns to classify budget categories',
                        },
                        {
                            'title': 'Variance Analysis',
                            'language': 'Python',
                            'description': 'Calculates spending variance to detect anomalies',
                        },
                    ],
                },
                {
                    'category': 'System Architecture',
                    'icon': 'fas fa-sitemap',
                    'skills': [
                        'Service-Oriented Architecture (SOA) design',
                        'Django ORM optimization with select_related/prefetch_related',
                        'RESTful API design for frontend integration',
                        'Database indexing for high-performance queries',
                    ],
                },
                {
                    'category': 'Testing & Quality',
                    'icon': 'fas fa-check-circle',
                    'skills': [
                        'Test-Driven Development (TDD) with Django TestCase',
                        '40 comprehensive unit and integration tests',
                        'Regression testing for backward compatibility',
                        '100% test pass rate',
                    ],
                },
            ],
            'problem_solving_stories': [
                {
                    'title': 'Query Optimization',
                    'problem': 'Transaction analysis queries timing out on $1.49M dataset',
                    'solution': 'Implemented select_related, added indexes, optimized aggregations',
                    'skills': ['PostgreSQL', 'Query Optimization', 'Django ORM'],
                    'outcome': '10x performance improvement, <2s response time',
                },
            ],
        }
    
    def get_recruiter_context(self):
        return {
            'subtitle': 'Demonstrating Leadership, Innovation & Measurable Business Impact',
            'achievements': [
                {
                    'category': 'Business Impact',
                    'icon': 'fas fa-trophy',
                    'metrics': [
                        {'label': 'Cost Savings', 'value': '$50K+/year', 'description': 'Reduced manual approval costs'},
                        {'label': 'Time Saved', 'value': '40 hours/month', 'description': 'Automation of routine tasks'},
                        {'label': 'Efficiency Gain', 'value': '75%', 'description': 'Auto-approval rate achieved'},
                        {'label': 'Accuracy', 'value': '95%+', 'description': 'Correct tier classifications'},
                    ],
                },
                {
                    'category': 'Technical Leadership',
                    'icon': 'fas fa-users-cog',
                    'accomplishments': [
                        'Designed and implemented AI-driven tier classification system from scratch',
                        'Led end-to-end development: requirements → design → implementation → testing → deployment',
                        'Created comprehensive test suite with 40 tests ensuring 100% pass rate',
                        'Optimized deployment process, reducing slug size by 87%',
                    ],
                },
            ],
            'skills_demonstrated': {
                'technical_skills': [
                    'Python/Django', 'PostgreSQL/SQL', 'AI/ML Algorithms', 'RESTful APIs',
                    'jQuery/AJAX', 'Git/Version Control', 'Heroku/Cloud Deployment',
                    'Test-Driven Development', 'System Architecture', 'Performance Optimization',
                ],
                'soft_skills': [
                    'Problem Solving', 'Technical Leadership', 'Project Management',
                    'Requirements Analysis', 'Innovation', 'Critical Thinking',
                ],
            },
            'timeline': [
                {'phase': 'Phase 1: Data Analysis', 'duration': '1 week', 'outcome': '$1.49M transactions analyzed, 95.6% categorized'},
                {'phase': 'Phase 2: Design & Architecture', 'duration': '3 days', 'outcome': 'Service layer designed, tier model created'},
                {'phase': 'Phase 3: Implementation', 'duration': '1 week', 'outcome': 'Core features built, 40 tests written'},
                {'phase': 'Phase 4: Testing & Deployment', 'duration': '2 days', 'outcome': 'Deployed to UAT, production-ready'},
            ],
        }


# Register this service
ProjectRegistry.register('budget-tier', BudgetTierPresentationService)

