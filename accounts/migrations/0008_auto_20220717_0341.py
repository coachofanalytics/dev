# Generated by Django 3.2.6 on 2022-07-17 08:41

import accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_merge_20220717_0340'),
    ]

    operations = [
        migrations.AddField(
            model_name='credential',
            name='user_type',
            field=models.CharField(choices=[('Superuser', 'Superuser'), ('Admin', 'Admin'), ('Employee', 'Employee'), ('Other', 'Other')], default='Other', max_length=25),
        ),
        migrations.AlterField(
            model_name='credentialcategory',
            name='department',
            field=models.ForeignKey(default=accounts.models.Department.get_default_pk, on_delete=django.db.models.deletion.CASCADE, to='accounts.department'),
        ),
    ]
