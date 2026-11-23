from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from users.forms import CustomRegisterForm

User = get_user_model()

class UserAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_creates_inactive_user_and_sends_email(self):
        response = self.client.post(reverse('sign-up'), {
            'username': 'newstudent',
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'newstudent@example.com',
            'contact': '01712345678',
            'password1': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('sign-in'))
        
        user = User.objects.get(username='newstudent')
        self.assertFalse(user.is_active)
        self.assertEqual(user.contact, '01712345678')

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Activate Your Account", mail.outbox[0].subject)
        self.assertIn(str(user.id), mail.outbox[0].body)

        # Verify token activation
        token = default_token_generator.make_token(user)
        activate_url = reverse('activate_user', kwargs={'user_id': user.id, 'token': token})
        act_response = self.client.get(activate_url)
        self.assertRedirects(act_response, reverse('sign-in'))

        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_contact_number_normalization(self):
        # Test +880 format
        form = CustomRegisterForm(data={
            'username': 'phoneuser1',
            'email': 'phone1@example.com',
            'contact': '+8801812345678',
            'password1': 'Pass123!456',
            'confirm_password': 'Pass123!456',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['contact'], '01812345678')

        # Test optional contact
        form_no_contact = CustomRegisterForm(data={
            'username': 'phoneuser2',
            'email': 'phone2@example.com',
            'contact': '',
            'password1': 'Pass123!456',
            'confirm_password': 'Pass123!456',
        })
        self.assertTrue(form_no_contact.is_valid(), form_no_contact.errors)

    def test_password_mismatch(self):
        form = CustomRegisterForm(data={
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password1': 'Password123!',
            'confirm_password': 'DifferentPass!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_password', form.errors)

    def test_signin_and_signout(self):
        user = User.objects.create_user(username='activeuser', password='Password123!', is_active=True)
        login_resp = self.client.post(reverse('sign-in'), {
            'username': 'activeuser',
            'password': 'Password123!'
        })
        self.assertRedirects(login_resp, reverse('home'))

        logout_resp = self.client.get(reverse('sign-out'))
        self.assertRedirects(logout_resp, reverse('home'))
