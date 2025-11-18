from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0022_update_fee_tier_defaults'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuggestedPositionOutcome',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('is_featured', models.BooleanField(default=False)),
                ('source', models.CharField(help_text='Origin of the idea (OptionPlay, Unusual Whales, manual)', max_length=20)),
                ('symbol', models.CharField(help_text='Underlying stock ticker', max_length=10)),
                ('strategy', models.CharField(help_text='Strategy at the time of suggestion (e.g., bull_put_spread)', max_length=30)),
                ('expiration_date', models.DateField(help_text='Expiration date associated with the suggestion')),
                ('premium_collected', models.DecimalField(blank=True, decimal_places=2, help_text='Net credit collected when the idea was suggested', max_digits=10, null=True)),
                ('capital_required', models.DecimalField(blank=True, decimal_places=2, help_text='Capital required for the suggested trade', max_digits=12, null=True)),
                ('probability_of_profit', models.DecimalField(blank=True, decimal_places=2, help_text='Probability of profit at suggestion time', max_digits=5, null=True)),
                ('underlying_close', models.DecimalField(blank=True, decimal_places=2, help_text='Underlying close price used for outcome calculation', max_digits=10, null=True)),
                ('realized_pnl', models.DecimalField(blank=True, decimal_places=2, help_text='Realized P&L (per suggestion) at expiration', max_digits=12, null=True)),
                ('return_pct', models.DecimalField(blank=True, decimal_places=2, help_text='Return as percentage of capital required', max_digits=7, null=True)),
                ('evaluated_at', models.DateTimeField(blank=True, help_text='Timestamp when the outcome was evaluated', null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending Outcome'), ('won', 'Profitable Outcome'), ('lost', 'Loss Outcome'), ('breakeven', 'Breakeven'), ('unsupported', 'Unsupported Strategy'), ('error', 'Calculation Error')], default='pending', help_text='Outcome classification', max_length=20)),
                ('calculation_notes', models.TextField(blank=True, help_text='Notes, errors, or rationale used to determine outcome')),
                ('data_snapshot', models.JSONField(blank=True, default=dict, help_text='Snapshot of legs/greeks at time of evaluation')),
                ('suggestion', models.OneToOneField(help_text='Suggestion this outcome belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='outcome_record', to='investing.suggestedposition')),
            ],
            options={
                'verbose_name': 'Suggested Position Outcome',
                'verbose_name_plural': 'Suggested Position Outcomes',
                'ordering': ['-expiration_date', 'symbol'],
            },
        ),
        migrations.AddIndex(
            model_name='suggestedpositionoutcome',
            index=models.Index(fields=['source', 'status'], name='sp_outcome_source_status_idx'),
        ),
        migrations.AddIndex(
            model_name='suggestedpositionoutcome',
            index=models.Index(fields=['symbol', 'expiration_date'], name='sp_outcome_symbol_expiry_idx'),
        ),
    ]




