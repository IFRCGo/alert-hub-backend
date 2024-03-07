import datetime

import django
from django.contrib.auth.middleware import (
    AuthenticationMiddleware as DjangoAuthenticationMiddleware,
)
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import (
    MessageMiddleware as DjangoMessageMiddleware,
)
from django.contrib.sessions.middleware import (
    SessionMiddleware as DjangoSessionMiddleware,
)
from django.http import JsonResponse
from graphql_jwt.settings import jwt_settings

from user_dir.utils import InvalidJwtIdError


class _GraphqlDisabledMiddlewareMixin:
    @staticmethod
    def is_graphql_request(request):
        return request.path_info.startswith("/graphql")

    def process_request(self, request):
        if self.is_graphql_request(request):
            return None
        try:
            return super().process_request(request)
        except AttributeError:
            return None

    def process_response(self, request, response):
        if self.is_graphql_request(request):
            return response
        try:
            return super().process_response(request, response)
        except AttributeError:
            return response


def django_logout(request):
    pass


class AuthenticationMiddleware(
    _GraphqlDisabledMiddlewareMixin, DjangoAuthenticationMiddleware
):
    def process_request(self, request):
        if self.is_graphql_request(request):
            if request.user.should_logout:
                django_logout(request)
            request.user = AnonymousUser()

        return super().process_request(request)


class SessionMiddleware(_GraphqlDisabledMiddlewareMixin, DjangoSessionMiddleware):
    pass


class MessageMiddleware(_GraphqlDisabledMiddlewareMixin, DjangoMessageMiddleware):
    pass


class DeleteJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = None
        try:
            response = self.get_response(request)
        except InvalidJwtIdError:
            if hasattr(request, 'COOKIES') and jwt_settings.JWT_COOKIE_NAME in request.COOKIES:
                request.delete_jwt_cookie = True
                self.my_delete_cookie(response, jwt_settings.JWT_COOKIE_NAME)
            response = JsonResponse({'error': 'Invalid token provided. Please login again.'},
                                    status=401)
        # type: ignore
        except Exception as exeception:
            if "NoneType object has no attribute 'is_authenticated'" in str(exeception):
                if hasattr(request, 'COOKIES') and jwt_settings.JWT_COOKIE_NAME in request.COOKIES:
                    request.delete_jwt_cookie = True
                    self.my_delete_cookie(response, jwt_settings.JWT_COOKIE_NAME)
                response = JsonResponse({'error': 'Invalid token provided. Please login again.'},
                                        status=401)
            if "Invalid token" in str(exeception):
                if hasattr(request, 'COOKIES') and jwt_settings.JWT_COOKIE_NAME in request.COOKIES:
                    request.delete_jwt_cookie = True
                    self.my_delete_cookie(response, jwt_settings.JWT_COOKIE_NAME)
                response = JsonResponse({'error': 'Invalid token provided. Please login again.'},
                                        status=401)
            if "Invalid token" in str(exeception):
                if hasattr(request, 'COOKIES') and jwt_settings.JWT_COOKIE_NAME in request.COOKIES:
                    request.delete_jwt_cookie = True
                response = JsonResponse({'error': 'Invalid token provided. Please login again.'},
                                        status=401)

        if response is None:
            response = JsonResponse({'error': 'Unknown error'}, status=500)

        if hasattr(request, 'delete_jwt_cookie') and request.delete_jwt_cookie:
            self.my_delete_cookie(response, jwt_settings.JWT_COOKIE_NAME)

        return response

    def process_response(self, request, response):
        if hasattr(request, 'delete_jwt_cookie') and request.delete_jwt_cookie:
            self.my_delete_cookie(response, jwt_settings.JWT_COOKIE_NAME)
        return response

    def my_delete_cookie(self, response, key):
        kwargs = {
            "path": jwt_settings.JWT_COOKIE_PATH,
            "domain": jwt_settings.JWT_COOKIE_DOMAIN,
        }

        if django.VERSION >= (2, 1):
            kwargs["samesite"] = jwt_settings.JWT_COOKIE_SAMESITE

        response.delete_cookie(key, **kwargs)
        expiration_time = datetime.datetime.now() - datetime.timedelta(days=1)

        # Use set_cookie() to set the cookie with the past expiration time
        response.set_cookie(key, value="", expires=expiration_time, **kwargs)
