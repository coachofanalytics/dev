from django.test import TestCase
from communities.models import CommunityMember, ForumCategory, Post, ContactMessage


class CommunityModelsTests(TestCase):
    def test_community_member_str(self):
        cm = CommunityMember.objects.create(name='Sam', email='sam@example.com')
        self.assertIn('sam@example.com', str(cm))

    def test_forumcategory_and_post_str(self):
        cat = ForumCategory.objects.create(name='News', slug='news', description='desc')
        post = Post.objects.create(title='Hello', content='c', category=cat)
        self.assertEqual(str(cat), 'News')
        self.assertEqual(str(post), 'Hello')

    def test_contact_message_str(self):
        cm = ContactMessage.objects.create(name='P', email='p@e.com', message='hi')
        self.assertIn('Message from P', str(cm))
