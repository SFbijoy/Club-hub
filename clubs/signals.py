from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from clubs.models import ClubMembership, ClubRole, Club

@receiver(post_save, sender=ClubMembership)
def send_membership_confirmation(sender, instance, created, **kwargs):
    if created and not instance.confirmed:
        token = default_token_generator.make_token(instance.user)
        confirmation_link = f"{settings.FRONTEND_URL}/clubs/membership/confirm/{instance.id}/{token}/"
        
        subject = f"Confirm your membership for {instance.club.name}"
        message = f"Hi {instance.user.username},\n\nPlease confirm your membership by clicking this link: {confirmation_link}\n\nThank you!"
        recipient_list = [instance.user.email]
        
        try:
            from_email = getattr(settings, 'EMAIL_HOST_USER', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@clubhub.com')
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            print(f"Failed to send email to {instance.user.email}: {e}")

@receiver(post_save, sender=ClubMembership)
def assign_default_role(sender, instance, created, **kwargs):
    if created and not instance.role:
        default_role = ClubRole.objects.filter(club=instance.club, role_name="Member").first()
        if default_role:
            ClubMembership.objects.filter(pk=instance.pk).update(role=default_role)
            instance.role = default_role
