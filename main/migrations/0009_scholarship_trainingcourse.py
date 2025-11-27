from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_scholarship_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='scholarship',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='scholarship',
            name='amount',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='scholarship',
            name='field',
            field=models.CharField(blank=True, choices=[('STEM', 'STEM'), ('Humanities', 'Humanities'), ('Business', 'Business'), ('Arts', 'Arts')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='scholarship',
            name='level',
            field=models.CharField(blank=True, choices=[('Undergraduate', 'Undergraduate'), ('Masters', 'Masters'), ('PhD', 'PhD'), ('Vocational', 'Vocational')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='scholarship',
            name='location',
            field=models.CharField(blank=True, choices=[('Kenya', 'Kenya'), ('Global', 'Global'), ('UK', 'UK'), ('USA', 'USA')], max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='scholarship',
            name='provider',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='scholarship',
            name='status',
            field=models.CharField(blank=True, choices=[('Open', 'Open'), ('Closing Soon', 'Closing Soon'), ('Closed', 'Closed')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='scholarship',
            name='title',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='scholarship',
            name='deadline',
            field=models.DateField(blank=True, null=True),
        ),
    ]

