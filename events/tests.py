from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date
from events.models import Event, EventAttendance
from clubs.models import Club

User = get_user_model()

class EventTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username='staffuser', password='Password123!', is_staff=True)
        self.normal_user = User.objects.create_user(username='normaluser', password='Password123!')
        self.event = Event.objects.create(
            title='Tech Fest 2026',
            description='Annual tech fest',
            date=date.today(),
            created_by=self.staff_user
        )

    def test_create_event_staff_only(self):
        self.client.login(username='normaluser', password='Password123!')
        resp = self.client.post(reverse('create-event'), {
            'title': 'Unauthorized Event',
            'date': '2026-12-01',
        })
        self.assertRedirects(resp, reverse('event-list'))

        self.client.login(username='staffuser', password='Password123!')
        resp2 = self.client.post(reverse('create-event'), {
            'title': 'Official Workshop',
            'event_type': 'general',
            'date': '2026-12-01',
        })
        new_event = Event.objects.get(title='Official Workshop')
        self.assertRedirects(resp2, reverse('event-detail', kwargs={'event_id': new_event.id}))

    def test_join_and_leave_event(self):
        self.client.login(username='normaluser', password='Password123!')
        join_resp = self.client.post(reverse('join-event', kwargs={'event_id': self.event.id}))
        self.assertRedirects(join_resp, reverse('event-detail', kwargs={'event_id': self.event.id}))

        attendance = EventAttendance.objects.get(event=self.event, user=self.normal_user)
        self.assertEqual(attendance.status, 'going')

        leave_resp = self.client.post(reverse('leave-event', kwargs={'event_id': self.event.id}))
        self.assertRedirects(leave_resp, reverse('event-detail', kwargs={'event_id': self.event.id}))
        self.assertFalse(EventAttendance.objects.filter(event=self.event, user=self.normal_user).exists())

    def test_event_capacity(self):
        self.event.max_capacity = 1
        self.event.save()

        # First user joins
        self.client.login(username='normaluser', password='Password123!')
        self.client.post(reverse('join-event', kwargs={'event_id': self.event.id}))

        # Second user tries to join but event is full
        self.client.login(username='staffuser', password='Password123!')
        resp = self.client.post(reverse('join-event', kwargs={'event_id': self.event.id}))
        self.assertRedirects(resp, reverse('event-detail', kwargs={'event_id': self.event.id}))
        self.assertFalse(EventAttendance.objects.filter(event=self.event, user=self.staff_user).exists())
