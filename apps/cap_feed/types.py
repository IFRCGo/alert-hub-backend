import typing
import strawberry
import strawberry_django
from django.db import models

from main.graphql.context import Info
from utils.strawberry.enums import enum_display_field, enum_field
from utils.strawberry.types import string_field
from utils.common import get_queryset_for_model
from .models import (
    Country,
    Alert,
    Admin1,
    Feed,
    Region,
    AlertInfo,
    Continent,
    AlertInfoParameter,
    AlertInfoArea,
    AlertInfoAreaPolygon,
    AlertInfoAreaCircle,
    AlertInfoAreaGeocode,
    LanguageInfo,
)


@strawberry_django.type(Region)
class RegionType:
    id: strawberry.ID

    name = string_field(Region.name)
    polygon = string_field(Region.polygon)
    centroid = string_field(Region.centroid)

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet | None, info: Info):
        return get_queryset_for_model(Region, queryset)


@strawberry_django.type(Continent)
class ContinentType:
    id: strawberry.ID
    name = string_field(Continent.name)


@strawberry_django.type(Country)
class CountryType:
    id: strawberry.ID

    name = string_field(Country.name)
    iso3 = string_field(Country.iso3)

    # TODO: Use custom type
    polygon = string_field(Country.polygon)
    multipolygon = string_field(Country.multipolygon)
    centroid = string_field(Country.centroid)

    if typing.TYPE_CHECKING:
        region_id = Country.region_id
        continent_id = Country.continent_id
    else:
        region_id: strawberry.ID
        continent_id: strawberry.ID

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet | None, info: Info):
        return get_queryset_for_model(Country, queryset)

    @strawberry.field
    async def region(self, info: Info) -> RegionType:
        return await info.context.dl.cap_feed.load_region.load(self.region_id)

    @strawberry.field
    async def continent(self, info: Info) -> ContinentType:
        return await info.context.dl.cap_feed.load_continent.load(self.continent_id)


@strawberry_django.type(Admin1)
class Admin1Type:
    id: strawberry.ID
    name = string_field(Admin1.name)

    # TODO: use custom type
    polygon = string_field(Admin1.polygon)
    multipolygon = string_field(Admin1.multipolygon)
    min_latitude = string_field(Admin1.min_latitude)
    max_latitude = string_field(Admin1.max_latitude)
    min_longitude = string_field(Admin1.min_longitude)
    max_longitude = string_field(Admin1.max_longitude)

    if typing.TYPE_CHECKING:
        country_id = Admin1.country_id
    else:
        country_id: strawberry.ID

    @strawberry.field
    async def country(self, info: Info) -> CountryType:
        return await info.context.dl.cap_feed.load_country.load(self.country_id)


@strawberry_django.type(LanguageInfo)
class LanguageInfoType:
    id: strawberry.ID
    feed_id: strawberry.ID
    name = string_field(LanguageInfo.name)
    logo = string_field(LanguageInfo.logo)
    language = string_field(LanguageInfo.language)


@strawberry_django.type(Feed)
class FeedType:
    id: strawberry.ID
    url = string_field(Feed.url)
    enable_polling: strawberry.auto
    enable_rebroadcast: strawberry.auto
    official: strawberry.auto
    author_name = string_field(Feed.author_name)
    author_email = string_field(Feed.author_email)
    notes = string_field(Feed.notes)

    # Enum
    format = enum_field(Feed.format)
    polling_interval = enum_field(Feed.polling_interval)
    status = enum_display_field(Feed.status)
    # -- Display
    format_display = enum_display_field(Feed.format)
    polling_interval_display = enum_field(Feed.polling_interval)
    status_display = enum_display_field(Feed.status)

    if typing.TYPE_CHECKING:
        pk: int
        country_id = Feed.country_id
    else:
        country_id: strawberry.ID

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet | None, info: Info):
        return get_queryset_for_model(Feed, queryset)

    @strawberry.field
    async def country(self, info: Info) -> CountryType:
        return await info.context.dl.cap_feed.load_country.load(self.country_id)

    @strawberry.field
    async def languages(self, info: Info) -> list[LanguageInfoType]:
        return await info.context.dl.cap_feed.load_language_info_by_feed.load(self.pk)


@strawberry_django.type(AlertInfoParameter)
class AlertInfoParameterType:
    id: strawberry.ID
    alert_info_id: strawberry.ID

    value_name = string_field(AlertInfoParameter.value_name)
    value = string_field(AlertInfoParameter.value)


@strawberry_django.type(AlertInfoAreaPolygon)
class AlertInfoAreaPolygonType:
    id: strawberry.ID
    alert_info_area_id: strawberry.ID

    value: strawberry.auto


@strawberry_django.type(AlertInfoAreaCircle)
class AlertInfoAreaCircleType:
    id: strawberry.ID
    alert_info_area_id: strawberry.ID

    value: strawberry.auto


@strawberry_django.type(AlertInfoAreaGeocode)
class AlertInfoAreaGeocodeType:
    id: strawberry.ID
    alert_info_area_id: strawberry.ID

    value_name = string_field(AlertInfoAreaGeocode.value_name)
    value = string_field(AlertInfoAreaGeocode.value)


@strawberry_django.type(AlertInfoArea)
class AlertInfoAreaType:
    id: strawberry.ID
    alert_info_id: strawberry.ID

    area_desc = string_field(AlertInfoArea.area_desc)
    altitude = string_field(AlertInfoArea.altitude)
    ceiling = string_field(AlertInfoArea.ceiling)

    if typing.TYPE_CHECKING:
        pk: int

    @strawberry.field
    async def polygons(self, info: Info) -> list[AlertInfoAreaPolygonType]:
        return await info.context.dl.cap_feed.load_info_area_polygons_by_info_area.load(self.pk)

    @strawberry.field
    async def circles(self, info: Info) -> list[AlertInfoAreaCircleType]:
        return await info.context.dl.cap_feed.load_info_area_circles_by_info_area.load(self.pk)

    @strawberry.field
    async def geocodes(self, info: Info) -> list[AlertInfoAreaGeocodeType]:
        return await info.context.dl.cap_feed.load_info_area_geocodes_by_info_area.load(self.pk)


@strawberry_django.type(AlertInfo)
class AlertInfoType:
    id: strawberry.ID
    alert_id: strawberry.ID

    language = string_field(AlertInfo.language)
    event = string_field(AlertInfo.event)
    audience = string_field(AlertInfo.audience)
    event_code = string_field(AlertInfo.event_code)
    sender_name = string_field(AlertInfo.sender_name)
    headline = string_field(AlertInfo.headline)
    description = string_field(AlertInfo.description)
    instruction = string_field(AlertInfo.instruction)
    web = string_field(AlertInfo.web)
    contact = string_field(AlertInfo.contact)
    parameter = string_field(AlertInfo.parameter)
    effective: strawberry.auto
    onset: strawberry.auto
    expires: strawberry.auto

    # Enum
    category = enum_field(AlertInfo.category)
    response_type = enum_field(AlertInfo.response_type)
    urgency = enum_field(AlertInfo.urgency)
    severity = enum_field(AlertInfo.severity)
    certainty = enum_field(AlertInfo.certainty)
    # -- Display
    category_display = enum_display_field(AlertInfo.category)
    response_type_display = enum_display_field(AlertInfo.response_type)
    urgency_display = enum_display_field(AlertInfo.urgency)
    severity_display = enum_display_field(AlertInfo.severity)
    effective: strawberry.auto
    onset: strawberry.auto
    expires: strawberry.auto
    certainty_display = enum_display_field(AlertInfo.certainty)

    if typing.TYPE_CHECKING:
        pk: int

    # TODO: Need to check if we need pagination instead
    @strawberry.field
    async def infos(self, info: Info) -> list[AlertInfoParameterType]:
        return await info.context.dl.cap_feed.load_info_parameters_by_info.load(self.pk)

    @strawberry.field
    async def areas(self, info: Info) -> list[AlertInfoAreaType]:
        return await info.context.dl.cap_feed.load_info_areas_by_info.load(self.pk)


@strawberry_django.type(Alert)
class AlertType:
    id: strawberry.ID

    url = string_field(Alert.url)
    identifier = string_field(Alert.identifier)
    sender = string_field(Alert.sender)
    sent: strawberry.auto
    source = string_field(Alert.source)
    scope = string_field(Alert.scope)
    restriction = string_field(Alert.restriction)
    addresses = string_field(Alert.addresses)
    code = string_field(Alert.code)
    note = string_field(Alert.note)
    references = string_field(Alert.references)
    incidents = string_field(Alert.incidents)

    if typing.TYPE_CHECKING:
        country_id = Alert.country_id
        feed_id = Alert.feed_id
    else:
        country_id: strawberry.ID
        feed_id: strawberry.ID

    # Enum
    status = enum_field(Alert.status)
    msg_type = enum_field(Alert.msg_type)
    # - Display
    status_display = enum_display_field(Alert.status)
    msg_type_display = enum_display_field(Alert.msg_type)

    if typing.TYPE_CHECKING:
        pk = Alert.pk

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet | None, info: Info):
        return get_queryset_for_model(Alert, queryset)

    @strawberry.field
    async def country(self: Alert, info: Info) -> CountryType:  # pyright: ignore[reportGeneralTypeIssues]
        return await info.context.dl.cap_feed.load_country.load(self.country_id)

    @strawberry.field
    async def feed(self, info: Info) -> FeedType:
        return await info.context.dl.cap_feed.load_feed.load(self.feed_id)

    # TODO: Need to check if we need pagination instead
    @strawberry.field
    async def admin1s(self, info: Info) -> list[Admin1Type]:
        return await info.context.dl.cap_feed.load_admin1s_by_alert.load(self.pk)

    # TODO: Need to check if we need pagination instead
    @strawberry.field
    async def infos(self, info: Info) -> list[AlertInfoType]:
        return await info.context.dl.cap_feed.load_infos_by_alert.load(self.pk)
