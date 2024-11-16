import abc

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


# WIP
class BaseTokenGenerator(abc.ABC, PasswordResetTokenGenerator):
    """
    Using PasswordResetTokenGenerator to create a reusable token generator clases
    """

    timeout = 3 * 86400  # (3 days, in seconds)
    key_salt: str

    def check_token(self, user, token):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self._make_token_with_timestamp(user, ts, secret),
                token,
            ):
                break
        else:
            return False

        # --- Custom code (Here we replace settings.PASSWORD_RESET_TIMEOUT with self.timeout)
        # https://github.com/django/django/blob/main/django/contrib/auth/tokens.py#L79
        # Check the timestamp is within limit.
        if (self._num_seconds(self._now()) - ts) > self.timeout:
            return False
        # --- Custom code

        return True

    @abc.abstractmethod
    def _make_hash_value(self, user, timestamp) -> str: ...
