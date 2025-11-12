import datetime
import logging
from collections import defaultdict
from xml.etree.ElementTree import Element as XmlElement

from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.measure import Distance
from django.db import IntegrityError, models
from django.utils import timezone

from apps.cap_feed.formats.utils import (
    convert_datetime,
    log_attributeerror,
    log_integrityerror,
    log_valueerror,
)
from apps.cap_feed.models import (
    Admin1,
    Alert,
    AlertAdmin1,
    AlertInfo,
    AlertInfoArea,
    AlertInfoAreaCircle,
    AlertInfoAreaGeocode,
    AlertInfoAreaPolygon,
    AlertInfoParameter,
    Feed,
    ProcessedAlert,
    alert_info_default_expire,
)
from apps.cap_feed.utils import distance_to_decimal_degrees
from main.managers import BulkCreateManager

logger = logging.getLogger(__name__)


def find_element(element, ns, tag):
    x = element.find(tag, ns)
    if x is not None and x.text:
        return x.text
    return None


def create_alert(
    feed: Feed,
    url: str,
    alert_root: XmlElement,
    ns: dict,
) -> Alert | None:
    alert_status = find_element(alert_root, ns, 'cap:status')
    if alert_status != 'Actual':
        return

    # TODO: Properly handle reportOptionalMemberAccess
    return Alert.objects.create(
        feed=feed,
        country=feed.country,
        url=url,
        identifier=alert_root.find('cap:identifier', ns).text,  # type: ignore[reportOptionalMemberAccess]
        sender=alert_root.find('cap:sender', ns).text,  # type: ignore[reportOptionalMemberAccess]
        sent=convert_datetime(alert_root.find('cap:sent', ns).text),  # type: ignore[reportOptionalMemberAccess]
        msg_type=alert_root.find('cap:msgType', ns).text,  # type: ignore[reportOptionalMemberAccess]
        source=find_element(alert_root, ns, 'cap:source'),
        scope=alert_root.find('cap:scope', ns).text,  # type: ignore[reportOptionalMemberAccess]
        restriction=find_element(alert_root, ns, 'cap:restriction'),
        addresses=find_element(alert_root, ns, 'cap:addresses'),
        references=find_element(alert_root, ns, 'cap:references'),
        code=find_element(alert_root, ns, 'cap:code'),
        note=find_element(alert_root, ns, 'cap:note'),
        incidents=find_element(alert_root, ns, 'cap:incidents'),
        status=alert_status,
    )


def create_alert_info(
    alert: Alert,
    alert_info_entry: XmlElement,
    expire_time: datetime.datetime | None,
    ns: dict,
) -> AlertInfo:
    # TODO: Properly handle reportOptionalMemberAccess

    return AlertInfo.objects.create(
        alert=alert,
        language=('en-US' if (x := alert_info_entry.find('cap:language', ns)) is None else x.text),
        category=alert_info_entry.find('cap:category', ns).text,  # type: ignore[reportOptionalMemberAccess]
        event=alert_info_entry.find('cap:event', ns).text,  # type: ignore[reportOptionalMemberAccess]
        response_type=find_element(alert_info_entry, ns, 'cap:responseType'),
        urgency=alert_info_entry.find('cap:urgency', ns).text,  # type: ignore[reportOptionalMemberAccess]
        severity=alert_info_entry.find('cap:severity', ns).text,  # type: ignore[reportOptionalMemberAccess]
        certainty=alert_info_entry.find('cap:certainty', ns).text,  # type: ignore[reportOptionalMemberAccess]
        audience=find_element(alert_info_entry, ns, 'cap:audience'),
        effective=(alert.sent if (x := alert_info_entry.find('cap:effective', ns)) is None else x.text),
        onset=convert_datetime(find_element(alert_info_entry, ns, 'cap:onset')),
        sender_name=find_element(alert_info_entry, ns, 'cap:senderName'),
        headline=find_element(alert_info_entry, ns, 'cap:headline'),
        description=find_element(alert_info_entry, ns, 'cap:description'),
        instruction=find_element(alert_info_entry, ns, 'cap:instruction'),
        web=find_element(alert_info_entry, ns, 'cap:web'),
        contact=find_element(alert_info_entry, ns, 'cap:contact'),
        expires=expire_time or alert_info_default_expire(),
    )


def process_alert_info(
    alert: Alert,
    alert_info_entry: XmlElement,
    mgr: BulkCreateManager,
    ns: dict,
) -> tuple[AlertInfo | None, list[GEOSGeometry], list[tuple[Point, int]]]:
    polygons: list[GEOSGeometry] = []
    circles: list[tuple[Point, int]] = []

    expire_time = convert_datetime(find_element(alert_info_entry, ns, 'cap:expires'))
    if expire_time is not None and expire_time < timezone.now():
        return None, polygons, circles

    alert_info = create_alert_info(alert, alert_info_entry, expire_time, ns)

    # navigate alert info parameter
    for alert_info_parameter_entry in alert_info_entry.findall('cap:parameter', ns):
        mgr.add(
            AlertInfoParameter(
                alert_info=alert_info,
                value_name=alert_info_parameter_entry.find('cap:valueName', ns).text,  # type: ignore[reportOptionalMemberAccess]  # noqa: E501
                value=alert_info_parameter_entry.find('cap:value', ns).text,  # type: ignore[reportOptionalMemberAccess]
            )
        )

    # navigate alert info area
    for alert_info_area_entry in alert_info_entry.findall('cap:area', ns):
        alert_info_area = AlertInfoArea.objects.create(
            alert_info=alert_info,
            area_desc=alert_info_area_entry.find('cap:areaDesc', ns).text,  # type: ignore[reportOptionalMemberAccess]
            altitude=find_element(alert_info_entry, ns, 'cap:altitude'),
            ceiling=find_element(alert_info_entry, ns, 'cap:ceiling'),
        )

        # navigate alert info area circle
        for alert_info_area_circle_entry in alert_info_area_entry.findall('cap:circle', ns):
            alert_info_area_circle = AlertInfoAreaCircle(
                alert_info_area=alert_info_area,
                value=alert_info_area_circle_entry.text,
            )
            mgr.add(alert_info_area_circle)
            if parsed_circle := alert_info_area_circle.get_geos():
                circles.append(parsed_circle)

        # navigate info area geocode
        for alert_info_area_geocode_entry in alert_info_area_entry.findall('cap:geocode', ns):
            mgr.add(
                AlertInfoAreaGeocode(
                    alert_info_area=alert_info_area,
                    value_name=alert_info_area_geocode_entry.find('cap:valueName', ns).text,  # type: ignore[reportOptionalMemberAccess]  # noqa: E501
                    value=alert_info_area_geocode_entry.find('cap:value', ns).text,  # type: ignore[reportOptionalMemberAccess]  # noqa: E501
                )
            )

        # navigate alert info area polygon
        for alert_info_area_polygon_entry in alert_info_area_entry.findall('cap:polygon', ns):
            if alert_info_area_polygon_entry is not None and alert_info_area_polygon_entry.text:
                alert_info_area_polygon = AlertInfoAreaPolygon(
                    alert_info_area=alert_info_area,
                    value=alert_info_area_polygon_entry.text.strip(),
                )
                mgr.add(alert_info_area_polygon)
                if parsed_polygon := alert_info_area_polygon.value_geojson:
                    polygons.append(parsed_polygon)
    return alert_info, polygons, circles


def process_geo_code_type(
    admin1_base_qs: models.QuerySet[Admin1], geocode_name: Admin1.GeoCode, values: set[str]
) -> list[int]:
    if geocode_name == Admin1.GeoCode.EMMA_ID:
        qs = admin1_base_qs.filter(emma_id__in=values)
    elif geocode_name == Admin1.GeoCode.NUTS1:
        qs = admin1_base_qs.filter(nuts1__in=values)
    elif geocode_name == Admin1.GeoCode.NUTS2:
        qs = admin1_base_qs.filter(nuts2__in=values)
    elif geocode_name == Admin1.GeoCode.NUTS3:
        qs = admin1_base_qs.filter(nuts3__in=values)
    elif geocode_name == Admin1.GeoCode.FIPS_CODE:
        qs = admin1_base_qs.filter(fips_code__in=values)
    return list(qs.values_list('id', flat=True))


def process_geo_codes(
    alert: Alert,
    admin1_base_qs: models.QuerySet[Admin1],
) -> list[int]:
    geocode_map: dict[Admin1.GeoCode, set[str]] = defaultdict(set)

    qs = AlertInfoAreaGeocode.objects.filter(alert_info_area__alert_info__alert=alert)
    for value_name, value in qs.values_list("value_name", "value"):
        # TODO: Remove _value2member_map_ after upgrading python version
        if value_name.upper() in Admin1.GeoCode._value2member_map_:
            geocode_map[Admin1.GeoCode[value_name.upper()]].add(value)

    possible_admin1_ids: list[int] = []
    for geocode_name, values in geocode_map.items():
        possible_admin1_ids.extend(process_geo_code_type(admin1_base_qs, geocode_name, values))

    return list(set(possible_admin1_ids))


def process_alert(
    url: str,
    alert_root: XmlElement,
    feed: Feed,
    ns: dict,
) -> Alert | None:
    alert = create_alert(feed, url, alert_root, ns)
    if alert is None:
        return

    mgr = BulkCreateManager()
    alert_has_valid_info = False
    alert_info_circles_collections = []
    tagged_admin1s_id = set()
    admin1_base_qs = Admin1.objects.filter(country=alert.country)

    # navigate alert info
    for alert_info_entry in alert_root.findall('cap:info', ns):
        alert_info, alert_info_polygons, alert_info_circles = process_alert_info(alert, alert_info_entry, mgr, ns)
        if not alert_info:
            continue
        alert_info_circles_collections.extend(alert_info_circles)

        alert_has_valid_info = True

        # XXX: Do we need to check circles as well?
        # check polygon intersection with admin1s
        for polygon in alert_info_polygons:
            possible_admin1s = admin1_base_qs.filter(
                # TODO: Check for performance issues
                geometry__intersects=polygon,
            ).exclude(id__in=tagged_admin1s_id)
            for admin1_id in possible_admin1s.values_list('id', flat=True):
                tagged_admin1s_id.add(admin1_id)
                mgr.add(
                    AlertAdmin1(
                        alert=alert,
                        admin1_id=admin1_id,
                    )
                )

    mgr.done()  # Make sure everything is saved to DB before we start tagging admin1s

    if alert_has_valid_info:
        # Fallback: Try circles
        if not tagged_admin1s_id:
            for circle in alert_info_circles_collections:
                possible_admin1s = admin1_base_qs.filter(
                    # TODO: Check for performance issues
                    geometry__dwithin=(
                        circle[0],
                        distance_to_decimal_degrees(
                            Distance(km=circle[1]),
                            circle[0],
                        ),
                    ),
                ).exclude(id__in=tagged_admin1s_id)
                for admin1_id in possible_admin1s.values_list('id', flat=True):
                    tagged_admin1s_id.add(admin1_id)
                    mgr.add(
                        AlertAdmin1(
                            alert=alert,
                            admin1_id=admin1_id,
                        )
                    )

        # Fallback: Try geocodes
        if not tagged_admin1s_id:
            for admin1_id in process_geo_codes(alert, admin1_base_qs):
                tagged_admin1s_id.add(admin1_id)
                mgr.add(
                    AlertAdmin1(
                        alert=alert,
                        admin1_id=admin1_id,
                    )
                )

        # Last fallback is Unknown admin1
        if not tagged_admin1s_id:
            if unknown_admin1 := admin1_base_qs.filter(name='Unknown').first():
                mgr.add(
                    AlertAdmin1(
                        alert=alert,
                        admin1=unknown_admin1,
                    )
                )

        alert.info_has_been_added()
        alert.save()

    mgr.done()
    if mrg_summary := mgr.summary(ignore_empty=True):
        logger.debug(f"DB ops summary for alert: {alert.pk}: {str(mrg_summary)}")
    return alert


def get_alert(url, alert_root, feed, ns) -> bool:
    alert = None
    try:
        alert = process_alert(url, alert_root, feed, ns)
        if alert:
            return True
    except AttributeError as e:
        logger.error('Failed to save alert', exc_info=True)
        log_attributeerror(feed, e, url)
    except IntegrityError as e:
        if 'duplicate key value' not in str(e):
            log_integrityerror(feed, e, url)
    except ValueError as e:
        logger.error('Failed to save alert', exc_info=True)
        log_valueerror(feed, e, url)
    finally:
        if alert is not None:
            # TODO: Do we need this?
            ProcessedAlert.objects.create(
                url=alert.url,
                feed=alert.feed,
            )
    return False
