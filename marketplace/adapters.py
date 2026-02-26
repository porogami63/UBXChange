"""Custom allauth adapters."""
from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    """Redirect superusers to Mod UI on login/signup."""

    def _redirect_for_superuser(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            return reverse('marketplace:mod_dashboard')
        return None

    def get_login_redirect_url(self, request):
        url = self._redirect_for_superuser(request)
        return url or super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        url = self._redirect_for_superuser(request)
        return url or super().get_signup_redirect_url(request)
