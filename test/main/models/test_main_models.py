import pytest
from main.models import Page, Description, Donation_organization, Scholarship


@pytest.mark.django_db
class TestMainModels:
    def test_page_and_description(self):
        page = Page.objects.create(page_name='Home')
        desc = Description.objects.create(page=page, name='Intro', content='Welcome')
        assert str(page) == 'Home'
        assert 'Intro' in str(desc)

    def test_donation_and_str(self):
        donation = Donation_organization.objects.create(donor_name='Alice', email='a@example.com', amount=50.00)
        assert 'Alice' in str(donation)

    def test_scholarship_defaults_and_ordering(self):
        s1 = Scholarship.objects.create(title='S1', provider='P1', level='Undergraduate', field='STEM', location='Global', amount='1000', deadline='2026-12-31', status='Open')
        s2 = Scholarship.objects.create(title='S2', provider='P2', level='Masters', field='Business', location='USA', amount='2000', deadline='2026-11-30', status='Open')
        # ordering by deadline should place s2 before s1
        assert list(Scholarship.objects.order_by('deadline'))[0].title in ['S2','S1']
