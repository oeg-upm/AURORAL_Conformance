from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, resolve


class RequerirAutenticacionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path.startswith('/accounts/login/') and not request.path.startswith('/admin/'):
            return redirect(settings.LOGIN_URL)
        return self.get_response(request)