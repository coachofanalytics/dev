# Generated by Django 3.0.7 on 2020-10-30 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Picture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backgroundImage', models.ImageField(default='default.jpg', upload_to='background')),
            ],
        ),
    ]
