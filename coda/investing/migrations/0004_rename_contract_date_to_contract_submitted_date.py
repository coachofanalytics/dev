# Generated migration to align database with model
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0003_alter_investmentcontent_description_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='investor_information',
            old_name='contract_date',
            new_name='contract_submitted_date',
        ),
    ]

