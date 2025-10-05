"""
Management command to set up AI model configurations
"""

from django.core.management.base import BaseCommand
from ai_services.models import AIModelConfiguration, AIModelTypes


class Command(BaseCommand):
    help = 'Set up AI model configurations for the platform'

    def add_arguments(self, parser):
        parser.add_argument('--openai-key', type=str, help='OpenAI API key')
        parser.add_argument('--claude-key', type=str, help='Claude API key')
        parser.add_argument('--reset', action='store_true', help='Reset all configurations')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Setting up AI Model Configurations...'))

        if options['reset']:
            self.stdout.write(self.style.WARNING('🧹 Resetting all AI model configurations...'))
            AIModelConfiguration.objects.all().delete()

        # Create GPT-4 Primary Configuration
        gpt4_config, created = AIModelConfiguration.objects.get_or_create(
            model_name=AIModelTypes.GPT4_PRIMARY,
            defaults={
                'is_active': True,
                'priority_order': 1,
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'api_key': options.get('openai_key', ''),
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created GPT-4 Primary configuration'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  GPT-4 Primary configuration already exists'))

        # Create GPT-3.5 Fallback Configuration
        gpt35_config, created = AIModelConfiguration.objects.get_or_create(
            model_name=AIModelTypes.GPT35_FALLBACK,
            defaults={
                'is_active': True,
                'priority_order': 2,
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'api_key': options.get('openai_key', ''),
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created GPT-3.5 Fallback configuration'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  GPT-3.5 Fallback configuration already exists'))

        # Create Claude-3 Backup Configuration
        claude_config, created = AIModelConfiguration.objects.get_or_create(
            model_name=AIModelTypes.CLAUDE3_BACKUP,
            defaults={
                'is_active': False,  # Disabled by default until API key is provided
                'priority_order': 3,
                'api_endpoint': 'https://api.anthropic.com/v1/messages',
                'api_key': options.get('claude_key', ''),
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created Claude-3 Backup configuration'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Claude-3 Backup configuration already exists'))

        # Create Local Offline Configuration
        local_config, created = AIModelConfiguration.objects.get_or_create(
            model_name=AIModelTypes.LOCAL_OFFLINE,
            defaults={
                'is_active': True,
                'priority_order': 4,
                'api_endpoint': 'http://localhost:8000/mock-ai-endpoint',
                'api_key': '',
                'max_tokens': 1000,
                'temperature': 0.3,
                'timeout_seconds': 30
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created Local Offline configuration'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Local Offline configuration already exists'))

        # Update API keys if provided
        if options.get('openai_key'):
            AIModelConfiguration.objects.filter(
                model_name__in=[AIModelTypes.GPT4_PRIMARY, AIModelTypes.GPT35_FALLBACK]
            ).update(api_key=options['openai_key'])
            self.stdout.write(self.style.SUCCESS('🔑 Updated OpenAI API keys'))

        if options.get('claude_key'):
            AIModelConfiguration.objects.filter(
                model_name=AIModelTypes.CLAUDE3_BACKUP
            ).update(
                api_key=options['claude_key'],
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('🔑 Updated Claude API key and activated'))

        # Display final status
        total_configs = AIModelConfiguration.objects.count()
        active_configs = AIModelConfiguration.objects.filter(is_active=True).count()
        
        self.stdout.write(self.style.SUCCESS(
            f'✅ AI Model Configuration Setup Complete!\n'
            f'   📊 Total Configurations: {total_configs}\n'
            f'   🟢 Active Configurations: {active_configs}\n'
            f'   🔧 Ready for AI integration with fallback support'
        ))

        # Display configuration summary
        self.stdout.write(self.style.HTTP_INFO('\n📋 Configuration Summary:'))
        for config in AIModelConfiguration.objects.all().order_by('priority_order'):
            status = '🟢 Active' if config.is_active else '🔴 Inactive'
            api_key_status = '🔑 Configured' if config.api_key else '❌ No API Key'
            self.stdout.write(f'   {config.model_name}: {status} | {api_key_status} | Priority: {config.priority_order}')


