from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from clubs.models import Club, ClubMembership, ClubRole

User = get_user_model()

class ClubTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username='staffuser', password='Password123!', is_staff=True)
        self.normal_user = User.objects.create_user(username='normaluser', password='Password123!')
        self.other_user = User.objects.create_user(username='otheruser', password='Password123!')

    def test_create_club_assigns_president_role(self):
        self.client.login(username='staffuser', password='Password123!')
        response = self.client.post(reverse('create-club'), {
            'name': 'Robotics Club',
            'description': 'A club for robotics lovers.',
        })
        club = Club.objects.get(name='Robotics Club')
        self.assertRedirects(response, reverse('club-detail', kwargs={'club_id': club.id}))

        # Verify creator is confirmed member and has President role
        membership = ClubMembership.objects.get(club=club, user=self.staff_user)
        self.assertTrue(membership.confirmed)
        self.assertEqual(membership.role.role_name, 'President')

    def test_normal_user_cannot_create_club(self):
        self.client.login(username='normaluser', password='Password123!')
        response = self.client.post(reverse('create-club'), {
            'name': 'Hacker Club',
            'description': 'Description',
        })
        self.assertRedirects(response, reverse('club-list'))
        self.assertFalse(Club.objects.filter(name='Hacker Club').exists())

    def test_join_and_approve_membership(self):
        club = Club.objects.create(name='IT Club', description='IT Club desc')
        ClubRole.objects.create(club=club, role_name='President')
        ClubRole.objects.create(club=club, role_name='Member')

        # Normal user requests to join
        self.client.login(username='normaluser', password='Password123!')
        join_resp = self.client.post(reverse('join-club', kwargs={'club_id': club.id}))
        self.assertRedirects(join_resp, reverse('club-detail', kwargs={'club_id': club.id}))

        membership = ClubMembership.objects.get(club=club, user=self.normal_user)
        self.assertFalse(membership.confirmed)

        # Other normal user cannot approve
        self.client.login(username='otheruser', password='Password123!')
        appr_resp = self.client.get(reverse('approve-member', kwargs={'membership_id': membership.id}))
        self.assertRedirects(appr_resp, reverse('club-detail', kwargs={'club_id': club.id}))
        membership.refresh_from_db()
        self.assertFalse(membership.confirmed)

        # Staff can approve
        self.client.login(username='staffuser', password='Password123!')
        appr_resp2 = self.client.get(reverse('approve-member', kwargs={'membership_id': membership.id}))
        self.assertRedirects(appr_resp2, reverse('pending-requests', kwargs={'club_id': club.id}))
        membership.refresh_from_db()
        self.assertTrue(membership.confirmed)

    def test_token_confirm_membership(self):
        club = Club.objects.create(name='Drama Club')
        membership = ClubMembership.objects.create(club=club, user=self.normal_user, confirmed=False)
        token = default_token_generator.make_token(self.normal_user)

        url = reverse('confirm-membership', kwargs={'membership_id': membership.id, 'token': token})
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('club-detail', kwargs={'club_id': club.id}))
        membership.refresh_from_db()
        self.assertTrue(membership.confirmed)

    def test_delete_club_permission(self):
        club = Club.objects.create(name='Chess Club')
        # Normal user cannot delete
        self.client.login(username='normaluser', password='Password123!')
        del_resp = self.client.post(reverse('delete-club', kwargs={'club_id': club.id}))
        self.assertRedirects(del_resp, reverse('club-detail', kwargs={'club_id': club.id}))
        self.assertTrue(Club.objects.filter(id=club.id).exists())

        # Staff user can delete
        self.client.login(username='staffuser', password='Password123!')
        del_resp2 = self.client.post(reverse('delete-club', kwargs={'club_id': club.id}))
        self.assertRedirects(del_resp2, reverse('club-list'))
        self.assertFalse(Club.objects.filter(id=club.id).exists())
