import typing

import strawberry
from django.db import models
from django.db.models.fields import Field as DjangoBaseField

if typing.TYPE_CHECKING:
    from django.db.models.fields import _FieldDescriptor


GenericScalar = strawberry.scalar(
    typing.NewType("GenericScalar", typing.Any),  # type: ignore[reportGeneralTypeIssues]
    description="The GenericScalar scalar type represents a generic GraphQL scalar value that could be: List or Object.",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


def string_field(
    field: typing.Union[
        DjangoBaseField,
        models.query_utils.DeferredAttribute,
        '_FieldDescriptor',
    ]
):
    """
    Behaviour:
        blank = true, is_null = True
            - String (Null if empty)
        blank = true, is_null = false
            - String (Null if empty)
        blank = false, is_null = false
            - String!
    """

    _field = field
    if isinstance(field, models.query_utils.DeferredAttribute):
        _field = field.field

    def _get_value(root) -> None | str:
        return getattr(root, _field.attname)  # type: ignore[reportGeneralTypeIssues] FIXME

    @strawberry.field
    def string_(root) -> str:
        return _get_value(root)  # type: ignore[reportGeneralTypeIssues] FIXME

    @strawberry.field
    def nullable_string_(root) -> typing.Optional[str]:
        _value = _get_value(root)
        if _value == '':
            return
        return _value

    if _field.null or _field.blank:  # type: ignore[reportGeneralTypeIssues] FIXME
        return nullable_string_
    return string_
