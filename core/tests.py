from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date
from events.models import Event
from clubs.models import Club

User = get_user_model()

class CoreTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.club = Club.objects.create(name='BUBT Cultural Club', description='Cultural activities')
        self.event = Event.objects.create(
            title='Cultural Night',
            description='Celebration of culture',
            date=date.today(),
            club=self.club
        )

    def test_home_page_renders_without_images(self):
        # Event and Club have no images uploaded
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cultural Night')
        self.assertContains(response, 'BUBT Cultural Club')

    def test_search(self):
        response = self.client.get(reverse('search'), {'q': 'Cultural'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cultural Night')
        self.assertContains(response, 'BUBT Cultural Club')
