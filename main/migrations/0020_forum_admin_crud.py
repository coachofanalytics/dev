import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0019_community_messaging'),
    ]

    operations = [
        # Add author FK to CommunityPost
        migrations.AddField(
            model_name='communitypost',
            name='author',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='forum_posts',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Add updated_at field for tracking edits
        migrations.AddField(
            model_name='communitypost',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add related_name to category FK for easier queries
        migrations.AlterField(
            model_name='communitypost',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posts',
                to='main.forumcategory',
            ),
        ),
    ]
