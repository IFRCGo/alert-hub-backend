from dataclasses import dataclass
from strawberry.types import Info as _Info
from strawberry.django.context import StrawberryDjangoContext

from .dataloaders import GlobalDataLoader


@dataclass
class GraphQLContext(StrawberryDjangoContext):
    dl: GlobalDataLoader


# NOTE: This is for type support only, There is a better way?
class Info(_Info):
    context: GraphQLContext  # pyright: ignore[reportIncompatibleMethodOverride]
