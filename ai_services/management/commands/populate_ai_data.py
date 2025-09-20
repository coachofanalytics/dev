"""
Management command to populate AI services with high-quality test data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import secrets
from ai_services.models import (
    DiasporaAnalysisData, AnalysisSession, AIModelConfiguration,
    DiasporaAnalysisTypes, AIModelTypes
)


class Command(BaseCommand):
    help = 'Populate AI services with high-quality test data for demo purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sessions',
            type=int,
            default=50,
            help='Number of analysis sessions to create (default: 50)'
        )
        parser.add_argument(
            '--analyses',
            type=int,
            default=200,
            help='Number of analyses to create (default: 200)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting AI Services Data Population...')
        )

        # Clear existing data
        self.stdout.write('🧹 Clearing existing data...')
        DiasporaAnalysisData.objects.all().delete()
        AnalysisSession.objects.all().delete()
        AIModelConfiguration.objects.all().delete()

        # Create AI model configurations
        self.create_ai_configurations()

        # Create analysis sessions
        sessions_count = options['sessions']
        analyses_count = options['analyses']
        
        sessions = self.create_analysis_sessions(sessions_count)
        self.create_analysis_data(sessions, analyses_count)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully populated AI Services with:'
                f'\n   📊 {sessions_count} Analysis Sessions'
                f'\n   🔍 {analyses_count} AI Analyses'
                f'\n   ⚙️  {AIModelConfiguration.objects.count()} AI Model Configurations'
            )
        )

    def create_ai_configurations(self):
        """Create AI model configurations"""
        configurations = [
            {
                'model_name': AIModelTypes.GPT4_PRIMARY,
                'is_active': True,
                'priority_order': 1,
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'max_tokens': 2000,
                'temperature': 0.3,
                'timeout_seconds': 30,
            },
            {
                'model_name': AIModelTypes.GPT35_FALLBACK,
                'is_active': True,
                'priority_order': 2,
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'max_tokens': 1500,
                'temperature': 0.4,
                'timeout_seconds': 25,
            },
            {
                'model_name': AIModelTypes.CLAUDE3_BACKUP,
                'is_active': True,
                'priority_order': 3,
                'api_endpoint': 'https://api.anthropic.com/v1/messages',
                'max_tokens': 1800,
                'temperature': 0.35,
                'timeout_seconds': 35,
            },
            {
                'model_name': AIModelTypes.LOCAL_OFFLINE,
                'is_active': False,
                'priority_order': 4,
                'api_endpoint': 'http://localhost:8000/api/local-ai/',
                'max_tokens': 1000,
                'temperature': 0.5,
                'timeout_seconds': 60,
            },
        ]

        for config_data in configurations:
            AIModelConfiguration.objects.create(**config_data)

        self.stdout.write('✅ Created AI model configurations')

    def create_analysis_sessions(self, count):
        """Create realistic analysis sessions"""
        sessions = []
        stakeholder_types = ['investor', 'government', 'diaspora', 'general']
        countries = ['Kenya', 'USA', 'UK', 'Canada', 'Germany', 'Australia']
        
        for i in range(count):
            session_id = secrets.token_urlsafe(32)
            start_time = timezone.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            session = AnalysisSession.objects.create(
                session_id=session_id,
                start_time=start_time,
                end_time=start_time + timedelta(
                    minutes=random.randint(15, 120)
                ) if random.choice([True, False]) else None,
                total_analyses=random.randint(1, 8),
                user_agent=f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36',
                ip_address=f'{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}',
                country=random.choice(countries),
                is_completed=random.choice([True, False]),
                presentation_mode=random.choice([True, False]),
                stakeholder_type=random.choice(stakeholder_types)
            )
            sessions.append(session)

        self.stdout.write(f'✅ Created {count} analysis sessions')
        return sessions

    def create_analysis_data(self, sessions, count):
        """Create realistic analysis data"""
        analysis_types = [
            DiasporaAnalysisTypes.REMITTANCE_ANALYSIS,
            DiasporaAnalysisTypes.TRADE_FACILITATION,
            DiasporaAnalysisTypes.INVESTMENT_OPPORTUNITIES,
            DiasporaAnalysisTypes.EDUCATION_PATHWAYS,
            DiasporaAnalysisTypes.HEALTHCARE_ACCESS,
        ]

        model_types = [
            AIModelTypes.GPT4_PRIMARY,
            AIModelTypes.GPT35_FALLBACK,
            AIModelTypes.CLAUDE3_BACKUP,
        ]

        for i in range(count):
            session = random.choice(sessions)
            analysis_type = random.choice(analysis_types)
            model_used = random.choice(model_types)
            
            # Create realistic input data based on analysis type
            user_input = self.generate_realistic_input(analysis_type)
            
            # Create realistic AI prediction
            ai_prediction = self.generate_realistic_prediction(analysis_type, user_input)
            
            # Calculate realistic metrics
            confidence_score = random.uniform(0.75, 0.95)
            processing_time = random.uniform(1.5, 3.5)
            fallback_used = random.choice([True, False]) if model_used != AIModelTypes.GPT4_PRIMARY else False

            DiasporaAnalysisData.objects.create(
                session_id=session.session_id,
                analysis_type=analysis_type,
                user_input=user_input,
                ai_prediction=ai_prediction,
                model_used=model_used,
                confidence_score=confidence_score,
                processing_time=processing_time,
                fallback_used=fallback_used,
                created_at=session.start_time + timedelta(
                    minutes=random.randint(1, 60)
                ),
                is_active=True
            )

        self.stdout.write(f'✅ Created {count} analysis records')

    def generate_realistic_input(self, analysis_type):
        """Generate realistic input data based on analysis type"""
        if analysis_type == DiasporaAnalysisTypes.REMITTANCE_ANALYSIS:
            return {
                'amount': random.uniform(500, 5000),
                'frequency': random.choice(['weekly', 'monthly', 'quarterly']),
                'destination': random.choice(['Kenya', 'Uganda', 'Tanzania', 'Rwanda']),
                'purpose': random.choice(['family_support', 'investment', 'education', 'business']),
                'experience_years': random.randint(1, 20),
                'method': random.choice(['mobile_money', 'bank_transfer', 'money_transfer', 'crypto'])
            }
        elif analysis_type == DiasporaAnalysisTypes.TRADE_FACILITATION:
            return {
                'business_type': random.choice(['import', 'export', 'both']),
                'product_categories': random.sample(['agriculture', 'textiles', 'manufacturing', 'services', 'technology'], random.randint(1, 3)),
                'annual_volume': random.uniform(10000, 500000),
                'target_markets': random.sample(['USA', 'UK', 'Germany', 'France', 'Canada', 'China'], random.randint(1, 3)),
                'business_years': random.randint(1, 15),
                'challenges': random.sample(['logistics', 'regulations', 'financing', 'market_access', 'competition'], random.randint(1, 3))
            }
        elif analysis_type == DiasporaAnalysisTypes.INVESTMENT_OPPORTUNITIES:
            return {
                'investment_amount': random.uniform(5000, 100000),
                'risk_tolerance': random.choice(['low', 'medium', 'high']),
                'investment_horizon': random.choice(['1_year', '3_years', '5_years', '10_years']),
                'sector_interest': random.sample(['real_estate', 'agriculture', 'technology', 'manufacturing', 'services'], random.randint(1, 3)),
                'location_preference': random.choice(['Kenya', 'USA', 'UK', 'Canada'])
            }
        elif analysis_type == DiasporaAnalysisTypes.EDUCATION_PATHWAYS:
            return {
                'education_level': random.choice(['high_school', 'diploma', 'bachelor', 'master', 'phd']),
                'field_interest': random.choice(['technology', 'business', 'healthcare', 'education', 'engineering']),
                'budget': random.uniform(2000, 50000),
                'location_preference': random.choice(['Kenya', 'USA', 'UK', 'Canada']),
                'time_commitment': random.choice(['full_time', 'part_time', 'online'])
            }
        elif analysis_type == DiasporaAnalysisTypes.HEALTHCARE_ACCESS:
            return {
                'age_group': random.choice(['child', 'adult', 'senior']),
                'health_conditions': random.sample(['diabetes', 'hypertension', 'heart_disease', 'cancer', 'mental_health'], random.randint(0, 2)),
                'insurance_status': random.choice(['none', 'private', 'public', 'employer']),
                'location': random.choice(['Kenya', 'USA', 'UK', 'Canada']),
                'budget': random.uniform(1000, 20000)
            }

    def generate_realistic_prediction(self, analysis_type, user_input):
        """Generate realistic AI prediction based on input data"""
        # Calculate base score based on input quality
        base_score = 6.0
        
        if analysis_type == DiasporaAnalysisTypes.REMITTANCE_ANALYSIS:
            amount = user_input.get('amount', 1000)
            if amount >= 2000:
                base_score += 1.5
            elif amount >= 1000:
                base_score += 1.0
            
            if user_input.get('frequency') == 'monthly':
                base_score += 0.5
            if user_input.get('purpose') == 'investment':
                base_score += 0.5
                
            return {
                'assessment_score': min(10.0, base_score),
                'recommendations': [
                    f'Consider increasing monthly remittance to ${amount * 1.2:.0f} for maximum impact',
                    'Explore mobile money platforms like M-Pesa for lower transaction costs',
                    'Set up automated monthly transfers to ensure consistency',
                    'Consider diversifying remittance methods to reduce dependency',
                    'Build credit history through regular remittances for future loan opportunities'
                ],
                'risk_factors': [
                    'Currency fluctuation risks between USD and Kenyan Shilling',
                    'Regulatory changes in remittance policies',
                    'Dependency on single remittance method',
                    'Economic instability in destination country'
                ],
                'next_steps': [
                    'Set up automated remittance schedule',
                    'Explore Kenyan investment opportunities',
                    'Build relationship with local financial institutions',
                    'Consider insurance products for remittance protection'
                ]
            }
        elif analysis_type == DiasporaAnalysisTypes.TRADE_FACILITATION:
            volume = user_input.get('annual_volume', 50000)
            if volume >= 100000:
                base_score += 2.0
            elif volume >= 50000:
                base_score += 1.0
                
            return {
                'assessment_score': min(10.0, base_score),
                'recommendations': [
                    'Focus on organic certification for agricultural products to access premium markets',
                    'Partner with established logistics companies like DHL or FedEx',
                    'Explore e-commerce platforms like Amazon and eBay for direct sales',
                    'Obtain necessary export licenses and certifications',
                    'Build strategic partnerships with local suppliers'
                ],
                'risk_factors': [
                    'Seasonal demand fluctuations in target markets',
                    'Regulatory compliance requirements for exports',
                    'Competition from established suppliers',
                    'Currency exchange rate volatility',
                    'Supply chain disruptions'
                ],
                'next_steps': [
                    'Obtain necessary certifications and licenses',
                    'Develop strong online presence and marketing',
                    'Build strategic partnerships',
                    'Conduct market research in target countries'
                ]
            }
        elif analysis_type == DiasporaAnalysisTypes.INVESTMENT_OPPORTUNITIES:
            amount = user_input.get('investment_amount', 10000)
            if amount >= 50000:
                base_score += 2.0
            elif amount >= 25000:
                base_score += 1.5
            elif amount >= 10000:
                base_score += 1.0
                
            return {
                'assessment_score': min(10.0, base_score),
                'recommendations': [
                    'Consider real estate investment in Nairobi and Mombasa for steady returns',
                    'Explore fintech startups in Kenya for high-growth potential',
                    'Diversify between property (60%) and technology investments (40%)',
                    'Invest in Kenyan government bonds for stable income',
                    'Consider REITs for real estate exposure without direct ownership'
                ],
                'risk_factors': [
                    'Political stability concerns in Kenya',
                    'Currency devaluation risks',
                    'Market liquidity challenges',
                    'Regulatory changes affecting foreign investments',
                    'Economic downturns affecting property values'
                ],
                'next_steps': [
                    'Conduct thorough market research in target sectors',
                    'Connect with local investment advisors and brokers',
                    'Start with smaller investments to test the market',
                    'Set up proper legal structures for investments'
                ]
            }
        elif analysis_type == DiasporaAnalysisTypes.EDUCATION_PATHWAYS:
            level = user_input.get('education_level', 'high_school')
            if level in ['master', 'phd']:
                base_score += 1.5
            elif level == 'bachelor':
                base_score += 1.0
                
            return {
                'assessment_score': min(10.0, base_score),
                'recommendations': [
                    'Consider online programs from universities like MIT or Stanford',
                    'Explore coding bootcamps like General Assembly or Flatiron School',
                    'Look into scholarship programs for Kenyan students',
                    'Consider community college programs as stepping stones',
                    'Explore certification programs in your field of interest'
                ],
                'risk_factors': [
                    'High cost of international education',
                    'Visa and immigration challenges',
                    'Language barriers in some programs',
                    'Recognition of foreign degrees in Kenya',
                    'Competition for limited scholarship spots'
                ],
                'next_steps': [
                    'Research specific programs and admission requirements',
                    'Apply for scholarships and financial aid',
                    'Prepare for standardized tests (SAT, GRE, etc.)',
                    'Build strong application portfolio'
                ]
            }
        elif analysis_type == DiasporaAnalysisTypes.HEALTHCARE_ACCESS:
            insurance = user_input.get('insurance_status', 'none')
            if insurance != 'none':
                base_score += 1.5
                
            return {
                'assessment_score': min(10.0, base_score),
                'recommendations': [
                    'Consider private health insurance plans with comprehensive coverage',
                    'Explore telemedicine services for remote consultations',
                    'Look into health savings accounts (HSAs) for tax benefits',
                    'Consider joining group health plans through employers',
                    'Research preventive care programs and wellness initiatives'
                ],
                'risk_factors': [
                    'High cost of healthcare without insurance',
                    'Limited access to specialists in rural areas',
                    'Pre-existing condition exclusions',
                    'Network limitations with insurance providers',
                    'Emergency care costs and coverage gaps'
                ],
                'next_steps': [
                    'Compare different insurance plans and coverage options',
                    'Schedule preventive health screenings',
                    'Build emergency fund for healthcare expenses',
                    'Research healthcare providers in your area'
                ]
            }



