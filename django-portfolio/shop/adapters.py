# shop/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class AutoSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    If a social account's email matches an existing user, attach and log them in.
    """

    def pre_social_login(self, request, sociallogin):
        # If sociallogin already attached to a user, do nothing
        if sociallogin.is_existing:
            return

        # Attempt to get email from provider data
        email = None
        try:
            # common places
            email = sociallogin.account.extra_data.get("email")
        except Exception:
            email = None

        # fallback to sociallogin.email_addresses (allauth may populate)
        if not email:
            try:
                if sociallogin.email_addresses:
                    email = sociallogin.email_addresses[0].email
            except Exception:
                email = None

        if not email:
            return

        # Find existing user with that email (case-insensitive)
        try:
            user = User.objects.filter(email__iexact=email).first()
        except Exception:
            user = None

        # If user exists, connect social account to that user
        if user:
            sociallogin.connect(request, user)
