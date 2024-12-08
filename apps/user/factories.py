import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import User


class UserFactory(DjangoModelFactory):
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: f'{n}@xyz.com')
    password_text = fuzzy.FuzzyText(length=15)
    password = factory.PostGeneration(lambda user, *args, **kwargs: user.set_password(user.password_text))

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = User

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password_text = kwargs.pop('password_text')
        user = super()._create(model_class, *args, **kwargs)
        user.password_text = password_text  # If raw password is needed while testing
        return user
