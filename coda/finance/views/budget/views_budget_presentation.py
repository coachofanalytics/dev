"""
Budget Tier System Presentation Views

Provides presentation interfaces for:
- Investor pitches (ROI, cost savings)
- Technical interviews (AI/ML, architecture)
- Recruiter/HR (achievements, impact)
- Standard demos

Created: October 2025
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from finance.services.budget_tier_presentation_service import BudgetTierPresentationService


def budget_tier_presentation(request):
    """
    Main presentation dashboard with mode selection
    
    Query params:
        mode: investor|technical|recruiter|standard (default: standard)
    """
    presentation_mode = request.GET.get('mode', 'standard')
    
    # Get presentation context
    presentation_service = BudgetTierPresentationService()
    context = presentation_service.get_presentation_context(presentation_mode)
    
    # Add demo scenarios
    context['demo_scenarios'] = presentation_service.get_demo_scenarios()
    
    # Render appropriate template based on mode
    template_mapping = {
        'investor': 'finance/budgets/presentations/investor_presentation.html',
        'technical': 'finance/budgets/presentations/technical_presentation.html',
        'recruiter': 'finance/budgets/presentations/recruiter_presentation.html',
        'standard': 'finance/budgets/presentations/standard_presentation.html',
    }
    
    template = template_mapping.get(presentation_mode, template_mapping['standard'])
    return render(request, template, context)


def presentation_guide(request):
    """
    Comprehensive presentation guide with talking points
    """
    presentation_service = BudgetTierPresentationService()
    
    context = {
        'title': 'Budget Tier System - Presentation Guide',
        'presentation_modes': [
            {
                'mode': 'investor',
                'title': 'Investor Presentation',
                'description': 'Focus on ROI, cost savings, market opportunity',
                'audience': 'VCs, Angel Investors, Business Stakeholders',
                'duration': '15-20 minutes',
                'url': '/finance/budget-tier-presentation/?mode=investor',
            },
            {
                'mode': 'technical',
                'title': 'Technical Interview Presentation',
                'description': 'Showcase AI/ML skills, architecture, problem-solving',
                'audience': 'Hiring Managers, Technical Interviewers, CTOs',
                'duration': '20-30 minutes',
                'url': '/finance/budget-tier-presentation/?mode=technical',
            },
            {
                'mode': 'recruiter',
                'title': 'Recruiter/HR Presentation',
                'description': 'Highlight achievements, impact, leadership',
                'audience': 'Recruiters, HR Managers, Department Heads',
                'duration': '10-15 minutes',
                'url': '/finance/budget-tier-presentation/?mode=recruiter',
            },
            {
                'mode': 'standard',
                'title': 'Standard Demo',
                'description': 'General overview of features and capabilities',
                'audience': 'General Audience, Product Demos',
                'duration': '10 minutes',
                'url': '/finance/budget-tier-presentation/?mode=standard',
            },
        ],
        'talking_points': {
            'investor': [
                {
                    'section': 'Opening (2 min)',
                    'points': [
                        'Problem: Manual approvals cost $50K+/year in labor',
                        'Solution: AI-driven automation reduces costs by 75%',
                        'Market: $2.5B enterprise budget management market',
                    ],
                },
                {
                    'section': 'Demo (5 min)',
                    'points': [
                        'Show tier classification using real $1.49M dataset',
                        'Demo auto-approval for Tier A category',
                        'Show variance detection flagging anomaly',
                        'Highlight Finance Manager dashboard controls',
                    ],
                },
                {
                    'section': 'ROI & Metrics (5 min)',
                    'points': [
                        'Small org: $25K savings, 320% ROI, 3-month payback',
                        'Enterprise: $200K+ savings, 600% ROI, 6-week payback',
                        '95%+ accuracy, <2s processing time',
                    ],
                },
                {
                    'section': 'Competitive Advantage (3 min)',
                    'points': [
                        'Data-driven (not hardcoded rules)',
                        'Proven with $1.49M real transactions',
                        'Enterprise-ready (Django/PostgreSQL/Heroku)',
                    ],
                },
            ],
            'technical': [
                {
                    'section': 'Architecture Overview (5 min)',
                    'points': [
                        'Service-oriented architecture (SOA)',
                        'Three-layer design: Presentation → Service → Data',
                        'Django ORM optimization techniques',
                        'RESTful API design patterns',
                    ],
                },
                {
                    'section': 'AI/ML Implementation (10 min)',
                    'points': [
                        'Statistical pattern recognition algorithm',
                        'Time series analysis for recurring transactions',
                        'Variance modeling for anomaly detection',
                        'Multi-criteria classification (frequency, variance, amount)',
                        'Walk through tier classification code',
                    ],
                },
                {
                    'section': 'Testing & Quality (5 min)',
                    'points': [
                        'Test-Driven Development approach',
                        '40 comprehensive tests (unit + integration)',
                        '100% pass rate, regression coverage',
                        'Show test code examples',
                    ],
                },
                {
                    'section': 'Problem Solving Stories (5 min)',
                    'points': [
                        'Migration dependency hell → clean idempotent migration',
                        'Query timeout on $1.49M dataset → 10x optimization',
                        'Test environment issues → cross-platform setup',
                    ],
                },
            ],
            'recruiter': [
                {
                    'section': 'Impact Summary (3 min)',
                    'points': [
                        '$50K+ annual cost savings delivered',
                        '75% automation rate achieved',
                        '95%+ accuracy on 50+ categories',
                        '40 hours/month time savings',
                    ],
                },
                {
                    'section': 'Technical Leadership (5 min)',
                    'points': [
                        'End-to-end ownership: requirements → deployment',
                        'Led AI/ML implementation from scratch',
                        'Established DevOps best practices',
                        'Created comprehensive test suite',
                    ],
                },
                {
                    'section': 'Innovation & Problem Solving (5 min)',
                    'points': [
                        'Data-driven approach vs. traditional rules',
                        'Self-learning system improving with data',
                        'Resolved complex technical challenges',
                        'Optimized deployment (87% size reduction)',
                    ],
                },
            ],
        },
        'demo_flow': {
            'setup': [
                '1. Open presentation in fullscreen',
                '2. Have UAT environment ready (https://codamakutano.herokuapp.com)',
                '3. Login credentials prepared',
                '4. Browser console open (for technical demos)',
            ],
            'interactive_demos': [
                {
                    'title': 'Tier Classification Demo',
                    'steps': [
                        'Navigate to Tier Management Dashboard',
                        'Show 50+ categories with tier assignments',
                        'Highlight Tier A (auto), B (priority), C (manual)',
                        'Show typical amounts, variance thresholds',
                    ],
                },
                {
                    'title': 'Auto-Approval Demo',
                    'steps': [
                        'Create budget request for Tier A category (Utilities)',
                        'Amount: $5,200 (typical: $5,000, variance: 10%)',
                        'Show auto-approval in <2 seconds',
                        'Display approval log with reason',
                    ],
                },
                {
                    'title': 'Anomaly Detection Demo',
                    'steps': [
                        'Create budget request for Tier A category',
                        'Amount: $7,000 (typical: $5,000, variance: 10%)',
                        'Show system flags for manual review (+40% variance)',
                        'Display routing to appropriate approver',
                    ],
                },
            ],
        },
        'q_and_a': {
            'investor': [
                {'q': 'What's the market size?', 'a': '$2.5B enterprise budget management, 12% CAGR'},
                {'q': 'What's the payback period?', 'a': '2-3 months for most organizations'},
                {'q': 'How does it compare to competitors?', 'a': 'Data-driven vs. hardcoded rules, proven with $1.49M'},
            ],
            'technical': [
                {'q': 'What ML algorithms do you use?', 'a': 'Statistical analysis, time series, variance modeling, classification'},
                {'q': 'How do you handle edge cases?', 'a': 'Confidence scoring, fallback to manual review, configurable thresholds'},
                {'q': 'What's your test coverage?', 'a': '40 tests covering models, services, workflows, 100% pass rate'},
            ],
            'recruiter': [
                {'q': 'What was your biggest challenge?', 'a': 'Optimizing queries on $1.49M dataset, solved with 10x improvement'},
                {'q': 'What technologies did you use?', 'a': 'Python/Django, PostgreSQL, AI/ML algorithms, Heroku, Git'},
                {'q': 'What was the timeline?', 'a': '2 weeks: 1 week analysis, 1 week implementation, 2 days deployment'},
            ],
        },
    }
    
    return render(request, 'finance/budgets/presentations/presentation_guide.html', context)


def interactive_demo(request, demo_type):
    """
    Interactive demo endpoints for live presentations
    
    Args:
        demo_type: auto_approval|variance_detection|tier_classification
    """
    presentation_service = BudgetTierPresentationService()
    demos = presentation_service.get_demo_scenarios()
    
    demo = next((d for d in demos if d['id'] == demo_type), demos[0])
    
    context = {
        'demo': demo,
        'demo_type': demo_type,
    }
    
    return render(request, 'finance/budgets/presentations/interactive_demo.html', context)

