from django.core.exceptions import ValidationError
from django.utils.translation import gettext


class MaximumLengthValidator:
    def __init__(self, max_length=128):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                gettext(
                    "This password is too long. It must contain at most %(max_length)d characters.",
                ),
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_help_text(self):
        return gettext(
            "Your password must contain at most %(max_length)d characters.",
        ) % {"min_length": self.max_length}
