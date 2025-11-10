from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0021_add_position_entry_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='managedtradingaccount',
            name='fee_tier',
            field=models.CharField(
                choices=[
                    ('balanced', 'Balanced Automation - $249/mo + 12% over 6% hurdle'),
                    ('elite', 'Elite Desk (Coming Soon) - $399/mo + 18% over 5% hurdle'),
                    ('consultative', 'Consultative Coaching - Legacy $420 Plan'),
                    ('custom', 'Custom Fee Structure'),
                    ('starter', 'Starter - Legacy (inactive)'),
                    ('professional', 'Professional - Legacy (inactive)'),
                    ('premium', 'Premium - Legacy (inactive)'),
                    ('co_invest', 'Co-Investment - Legacy (inactive)'),
                ],
                default='balanced',
                help_text='Fee tier selected by client',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='feetierconfiguration',
            name='tier_code',
            field=models.CharField(
                choices=[
                    ('balanced', 'Balanced Automation - $249/mo + 12% over 6% hurdle'),
                    ('elite', 'Elite Desk (Coming Soon) - $399/mo + 18% over 5% hurdle'),
                    ('consultative', 'Consultative Coaching - Legacy $420 Plan'),
                    ('starter', 'Starter (Legacy)'),
                    ('professional', 'Professional (Legacy)'),
                    ('premium', 'Premium (Legacy)'),
                    ('co_invest', 'Co-Investment (Legacy)'),
                ],
                help_text='Unique identifier for this tier',
                max_length=20,
                unique=True,
            ),
        ),
    ]

