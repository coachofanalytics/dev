from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_servicerequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communitymember',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
    ]
