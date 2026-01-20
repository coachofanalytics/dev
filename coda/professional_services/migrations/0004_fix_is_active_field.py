# Fix is_active field type from integer to boolean

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('professional_services', '0003_fix_featured_category'),
    ]

    operations = [
        # Alter the is_active field from IntegerField to BooleanField
        migrations.AlterField(
            model_name='featuredcategory',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]