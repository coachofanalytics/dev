from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0019_add_auto_approval_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='suggestedposition',
            name='auto_approved_at',
            field=models.DateTimeField(blank=True, null=True, help_text='Timestamp when the system auto-approved this suggestion'),
        ),
        migrations.AddField(
            model_name='suggestedposition',
            name='auto_approved_by_system',
            field=models.BooleanField(default=False, help_text='True when the ranking engine auto-approved this suggestion without manual review'),
        ),
        migrations.AddField(
            model_name='suggestedposition',
            name='auto_approval_notes',
            field=models.TextField(blank=True, help_text='System-generated notes describing why this suggestion was auto-approved'),
        ),
    ]


