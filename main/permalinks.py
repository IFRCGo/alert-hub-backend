from django.conf import settings


class Permalink:
    BASE_URL = f'{settings.APP_FRONTEND_HOST}/permalink'

    FORGOT_PASSWORD = f'{BASE_URL}/forgot-password'

    @classmethod
    def user_password_reset(cls, uid: str, token: str):
        return f'{cls.BASE_URL}/user-password-reset/{uid}/{token}'

    @classmethod
    def user_activation(cls, uid: str, token: str):
        return f'{cls.BASE_URL}/user-activation/{uid}/{token}'

    @classmethod
    def subscription_detail(cls, id: int):
        return f'{cls.BASE_URL}/subscription-detail/{id}'

    @classmethod
    def alert_detail(cls, id: int):
        return f'{cls.BASE_URL}/alert-detail/{id}'

    @classmethod
    def unsubscribe_user_alert_subscription(cls, uid: str, token: str):
        return f'{cls.BASE_URL}/unsubscribe-user-alert-subscription/{uid}/{token}'
