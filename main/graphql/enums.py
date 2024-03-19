import strawberry
import dataclasses

from apps.user.enums import enum_map as user_enum_map
from apps.cap_feed.enums import enum_map as cap_feed_enum_map


ENUM_TO_STRAWBERRY_ENUM_MAP: dict[str, type] = {
    **user_enum_map,
    **cap_feed_enum_map,
}


class AppEnumData():
    def __init__(self, enum):
        self.enum = enum

    @property
    def key(self):
        return self.enum

    @property
    def label(self):
        return str(self.enum.label)


def generate_app_enum_collection_data(name):
    return type(
        name,
        (),
        {
            field_name: [
                AppEnumData(e)
                for e in enum
            ]
            for field_name, enum in ENUM_TO_STRAWBERRY_ENUM_MAP.items()
        },
    )


AppEnumCollectionData = generate_app_enum_collection_data('AppEnumCollectionData')


def generate_type_for_enum(name, Enum):
    return strawberry.type(
        dataclasses.make_dataclass(
            f'AppEnumCollection{name}',
            [
                ('key', Enum),
                ('label', str),
            ]
        )
    )


def _enum_type(name, Enum):
    EnumType = generate_type_for_enum(name, Enum)

    @strawberry.field
    def _field() -> list[EnumType]:  # pyright: ignore[reportGeneralTypeIssues]
        return [
            EnumType(
                key=e,
                label=e.label,
            )
            for e in Enum
        ]

    return list[EnumType], _field


def generate_type_for_enums():
    enum_fields = [
        (
            enum_field_name,
            *_enum_type(enum_field_name, enum),
        )
        for enum_field_name, enum in ENUM_TO_STRAWBERRY_ENUM_MAP.items()
    ]
    return strawberry.type(
        dataclasses.make_dataclass(
            'AppEnumCollection',
            enum_fields,
        )
    )


AppEnumCollection = generate_type_for_enums()
