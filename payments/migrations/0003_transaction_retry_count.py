# Generated migration for adding retry_count field to Transaction model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_subscriptionplan_billing_period_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='retry_count',
            field=models.IntegerField(default=0, help_text='Number of retry attempts for failed transactions'),
        ),
    ]
