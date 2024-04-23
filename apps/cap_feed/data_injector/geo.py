import glob
import os
import re

import requests
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from django.db import models, transaction

from apps.cap_feed.models import Admin1, Country, Region
from main.managers import BulkUpdateManager

module_dir = os.path.dirname(__file__)  # get current directory


class IfrcGoGeoInjector:
    """
    Utility to sync geo data from IFRC-GO
    - ifrc_go_id
    - name
    - bbox
    NOTE: New geo entities are not created. We just update existing ones
    """

    GO_DOMAIN = 'https://goadmin.ifrc.org'

    dj_cmd: BaseCommand | None
    region_map: dict[int, Region]  # Where int will be ifrc_go_id
    country_iso3_map: dict[str, Country]

    def __init__(self, django_cmd: BaseCommand | None = None):
        self.dj_cmd = django_cmd
        # This will be updated by respective injectors
        self.region_map = {}
        self.country_iso3_map = {}  # TODO: Use caseinsentive key

    def log_info(self, *messages: str):
        if self.dj_cmd:
            # TODO: handle int in messages
            self.dj_cmd.stdout.write(' '.join(messages))
            return
        # TODO: Use logger instead
        print(*messages)

    def log_success(self, *messages: str):
        if self.dj_cmd:
            self.dj_cmd.stdout.write(self.dj_cmd.style.SUCCESS(' '.join(messages)))
            return
        print(*messages)

    def log_warning(self, *messages: str):
        if self.dj_cmd:
            self.dj_cmd.stdout.write(self.dj_cmd.style.WARNING(' '.join(messages)))
            return
        print(*messages)

    def log_error(self, *messages: str):
        if self.dj_cmd:
            self.dj_cmd.stdout.write(self.dj_cmd.style.ERROR(' '.join(messages)))
            return
        print(*messages)

    @staticmethod
    def clean_name(name: str | None) -> str | None:
        if name is None:
            return

        return re.sub(
            ' +',
            ' ',
            name.replace('\n', ' '),
        ).strip()

    def handle_pagination(self, url, **requests_kwargs):
        _url = f'{self.GO_DOMAIN}{url}?limit=50'
        self.log_info('Fetching data from IFRC-GO:', _url)
        # TODO: Add some check to avoid infinite run
        while True:
            resp = requests.get(_url, **requests_kwargs).json()
            for item in resp['results']:
                yield item
            if resp['next'] is not None:
                _url = resp['next']
            else:
                break

    def inject_continents(self):
        # NOTE: Not required for now
        ...

    def inject_regions(self):
        go_data = self.handle_pagination('/api/v2/region/')

        for region_data in go_data:
            ifrc_go_id = region_data['id']
            region_name = self.clean_name(region_data['region_name'])

            region, created = Region.objects.filter(
                models.Q(ifrc_go_id=ifrc_go_id) | models.Q(name__iexact=region_name),
            ).get_or_create(
                defaults={
                    # 'name': region_name,
                },
            )

            region.ifrc_go_id = ifrc_go_id
            region.name = region_name
            region.bbox = GEOSGeometry(str(region_data['bbox']))
            region.save()
            self.region_map[region.ifrc_go_id] = region
            if created:
                self.log_success(f'Add region: {region}')
            else:
                self.log_success(f'Update region: {region}')

    def inject_countries(self):
        go_data = self.handle_pagination('/api/v2/country/')
        mgr = BulkUpdateManager(update_fields=['ifrc_go_id', 'name', 'region', 'bbox'])

        for country_data in go_data:
            ifrc_go_id = country_data['id']
            country_name = self.clean_name(country_data['name'])
            iso3 = country_data['iso3']
            bbox_raw = country_data['bbox']

            # NOTE: country_data['region'] is ifrc_go_id for region
            region = self.region_map.get(country_data['region'])
            if iso3 is None:
                self.log_warning(f'No iso3 found for {country_name}... skipping')
                continue
            if bbox_raw is None:
                self.log_warning(f'Empty bbox for {country_name}... skipping')
                continue
            if region is None:
                self.log_warning(f'No region found for {country_name}... skipping')
                continue

            country, created = Country.objects.filter(
                models.Q(ifrc_go_id=ifrc_go_id) | models.Q(iso3=iso3),
            ).get_or_create(
                defaults={
                    'iso3': iso3,
                    'name': country_name,
                    'region': region,
                }
            )

            country.ifrc_go_id = ifrc_go_id
            country.name = country_name
            country.region = region
            country.bbox = GEOSGeometry(str(bbox_raw))

            # country.save()
            mgr.add(country)
            self.country_iso3_map[country.iso3] = country
            if created:
                self.log_success(f'Create country: {country}')
            else:
                self.log_success(f'Update country: {country}')

        mgr.done()
        self.log_success(str(mgr.summary()))

    def inject_admin1s(self):
        mgr = BulkUpdateManager(update_fields=['ifrc_go_id', 'name', 'country', 'bbox', 'geometry'])

        def get_goejson_data():
            geojson_directory = os.path.join(os.path.dirname(module_dir), 'geographical/ifrc-go-admin1-geojson')
            all_files = glob.glob(geojson_directory + '/**/*.json', recursive=True)
            for file in all_files:
                layer = DataSource(file)[0]
                for feature in layer:
                    yield feature

        for feature in get_goejson_data():
            if feature.get('is_deprecated'):
                continue

            ifrc_go_id = feature.get('district_id')
            name = self.clean_name(feature.get('name'))
            iso3 = feature.get('iso3')
            country = self.country_iso3_map.get(iso3)

            # XXX: Save lower precision to avoid large geometry?
            geometry = feature.geom.wkt
            bbox = feature.geom.envelope.wkt

            if country is None:
                self.log_warning(f'No country found for {name}... skipping')
                continue

            admin1, created = Admin1.objects.filter(
                (models.Q(ifrc_go_id=ifrc_go_id) | models.Q(name=name)),
                country__iso3=iso3,
            ).get_or_create(
                defaults={
                    'country': country,
                    'name': name,
                }
            )

            # NOTE: Make sure all fields are included in mgr
            admin1.ifrc_go_id = ifrc_go_id
            admin1.name = name
            admin1.country = country
            admin1.bbox = bbox
            admin1.geometry = geometry

            mgr.add(admin1)
            if created:
                self.log_success(f'Create admin1: {admin1}')
            else:
                self.log_success(f'Update admin1: {admin1}')
        mgr.done()
        self.log_success(str(mgr.summary()))

    @transaction.atomic
    def sync(self):
        # NOTE: Inject order matters here
        self.inject_continents()
        self.inject_regions()
        self.inject_countries()
        self.inject_admin1s()
        # TODO: Show change summary


# inject region and country data if not already present
def inject_geographical_data():
    IfrcGoGeoInjector().sync()
