from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from .security import admin_second_factor_enabled


class AdminSecurityCodeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._needs_second_factor(request):
            verify_url = reverse("admin_security_code")
            return redirect(f"{verify_url}?next={request.get_full_path()}")

        return self.get_response(request)

    def _needs_second_factor(self, request):
        if not admin_second_factor_enabled():
            return False

        path = request.path
        protected = path.startswith("/admin/") or path.startswith("/dashboard/")
        exempt = path.startswith(settings.STATIC_URL) or path.startswith(settings.MEDIA_URL)
        exempt = exempt or path.startswith("/security-code/")
        if not protected or exempt:
            return False

        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and user.is_staff
            and not request.session.get("admin_second_factor_ok")
        )
