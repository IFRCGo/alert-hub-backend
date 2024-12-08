import typing

from django.contrib.auth.tokens import PasswordResetTokenGenerator

from utils.tokens import BaseTokenGenerator


def _generate_generator(name: str, _make_hash_value: None | typing.Callable = None, **kwargs):
    def _default_make_hash_func(_, user, timestamp):
        return str(user.pk) + str(timestamp)

    _name = f'{name}TokenGenerator'
    if _make_hash_value is None:
        _make_hash_value = _default_make_hash_func

    return type(
        _name,
        (BaseTokenGenerator,),
        dict(key_salt=_name, _make_hash_value=_make_hash_value, **kwargs),
    )()


def account_activation_token_generator_make_hash_value(_, user, timestamp):
    return str(user.pk) + str(user.is_active) + str(timestamp)


def user_subscription_unsubscribe_generator_make_hash_value(_, user_subscription, timestamp):
    return str(user_subscription.pk) + str(user_subscription.notify_by_email) + str(timestamp)


class TokenManager:
    password_reset_token_generator = PasswordResetTokenGenerator()
    account_activation_token_generator = _generate_generator(
        'AccountActivationTokenGenerator',
        timeout=7 * 86400,
        _make_hash_value=account_activation_token_generator_make_hash_value,
    )

    user_subscription_unsubscribe_generator = _generate_generator(
        'UserSubscriptionUnsubscribeGenerator',
        timeout=7 * 86400,
        _make_hash_value=user_subscription_unsubscribe_generator_make_hash_value,
    )
