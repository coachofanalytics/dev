import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0018_fix_communitymember_email_unique'),
    ]

    operations = [
        # Add user FK to CommunityMember
        migrations.AddField(
            model_name='communitymember',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='community_member',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Prevent one user from having multiple community profiles
        migrations.AddConstraint(
            model_name='communitymember',
            constraint=models.UniqueConstraint(
                condition=models.Q(('user__isnull', False)),
                fields=('user',),
                name='unique_user_community_member',
            ),
        ),
        # Create CommunityMessage model
        migrations.CreateModel(
            name='CommunityMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(blank=True, default='', max_length=200)),
                ('body', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='main.communitymember')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='main.communitymember')),
                ('parent_message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='main.communitymessage')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
