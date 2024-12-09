import requests
from django.conf import settings
from django.utils.translation import gettext
from rest_framework import serializers


def validate_hcaptcha(captcha):
    CAPTCHA_VERIFY_URL = 'https://hcaptcha.com/siteverify'

    data = {
        'sitekey': settings.HCAPTCHA_SITEKEY,
        'secret': settings.HCAPTCHA_SECRET,
        'response': captcha,
    }

    response = requests.post(url=CAPTCHA_VERIFY_URL, data=data)

    response_json = response.json()
    return response_json['success']


class CaptchaSerializerMixin(serializers.Serializer):
    captcha = serializers.CharField(write_only=True, required=True)

    def validate_captcha(self, captcha):
        if not validate_hcaptcha(captcha):
            raise serializers.ValidationError(gettext('Invalid captcha! Please, Try Again'))
