import pytest
from communities.models import ForumCategory, Post, CommentP
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCommunitiesModels:
    def test_forum_category_and_post(self):
        cat = ForumCategory.objects.create(name='General', slug='general', description='desc')
        post = Post.objects.create(title='Hello', content='World', category=cat)
        assert str(cat) == 'General'
        assert str(post) == 'Hello'

    def test_comment_create(self):
        user = User.objects.create(username='cuser')
        cat = ForumCategory.objects.create(name='General2', slug='g2', description='d')
        post = Post.objects.create(title='T', content='C', category=cat)
        comment = CommentP.objects.create(post=post, author=user, content='Nice')
        assert 'Nice' in comment.content
