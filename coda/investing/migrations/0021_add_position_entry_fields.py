from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0020_add_auto_flags_to_suggested_position'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='optionsposition',
            name='entered_at',
            field=models.DateTimeField(blank=True, help_text='When the trader confirmed this position is live.', null=True),
        ),
        migrations.AddField(
            model_name='optionsposition',
            name='entered_by',
            field=models.ForeignKey(blank=True, help_text='Trader who confirmed this position is live.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='entered_positions', to=settings.AUTH_USER_MODEL),
        ),
    ]

