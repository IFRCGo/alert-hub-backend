import json
import os
import re

import requests
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from django.db import models, transaction

from apps.cap_feed.models import Admin1, Continent, Country, Region
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
        self.country_iso3_map = {}

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
            region = Region.objects.filter(
                models.Q(ifrc_go_id=ifrc_go_id) | models.Q(name__iexact=region_name),
            ).first()
            if region is None:
                self.log_warning(f'No region found in the system for {region_name}... skipping')
                continue

            region.ifrc_go_id = ifrc_go_id
            region.name = region_name
            region.bbox = GEOSGeometry(str(region_data['bbox']))
            region.save()
            self.region_map[region.ifrc_go_id] = region
            self.log_success(f'Updating region: {region}')

    def inject_countries(self):
        go_data = self.handle_pagination('/api/v2/country/')
        mgr = BulkUpdateManager(update_fields=['ifrc_go_id', 'name', 'region', 'bbox'])

        for country_data in go_data:
            ifrc_go_id = country_data['id']
            country_name = self.clean_name(country_data['name'])
            iso3 = country_data['iso3']
            region = self.region_map.get(country_data['region'])
            if iso3 is None:
                self.log_warning(f'No iso3 found for {country_name}... skipping')
                continue
            if region is None:
                self.log_warning(f'No region found for {country_name}... skipping')
                continue

            country = Country.objects.filter(
                models.Q(ifrc_go_id=ifrc_go_id) | models.Q(iso3=iso3),
            ).first()
            if country is None:
                self.log_warning(f'No country found within the system for {country_name}... skipping')
                continue

            country.ifrc_go_id = ifrc_go_id
            country.name = country_name
            country.region = region
            country.bbox = GEOSGeometry(str(country_data['bbox']))
            country.save()
            mgr.add(country)
            self.country_iso3_map[country.iso3] = country
            self.log_success(f'Updating country: {country}')

        mgr.done()
        self.log_success(str(mgr.summary()))

    def inject_admin1s(self):
        go_data = self.handle_pagination('/api/v2/district/')
        mgr = BulkUpdateManager(update_fields=['ifrc_go_id', 'name', 'country', 'bbox'])

        for admin_data in go_data:
            if admin_data['is_deprecated']:
                continue

            ifrc_go_id = admin_data['id']
            admin1_name = self.clean_name(admin_data['name'])
            iso3 = admin_data['country_iso3']
            country = self.country_iso3_map.get(iso3)
            bbox_raw = admin_data['bbox']

            if country is None:
                self.log_warning(f'No country found for {admin1_name}... skipping')
                continue
            if bbox_raw is None:
                self.log_warning(f'No bbox found for {admin1_name}... skipping')
                continue

            admin1 = Admin1.objects.filter(
                (models.Q(ifrc_go_id=ifrc_go_id) | models.Q(name=admin1_name)),
                country__iso3=iso3,
            ).first()
            if admin1 is None:
                self.log_warning(f'No admin1 found within the system for {admin1_name}... skipping')
                continue

            admin1.ifrc_go_id = ifrc_go_id
            admin1.name = admin1_name
            admin1.country = country
            admin1.bbox = GEOSGeometry(str(bbox_raw))
            mgr.add(admin1)
            self.log_success(f'Updating admin1: {admin1}')
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


# inject continent data
def inject_continents(inject_path):
    def process_continents():
        for continent_entry in continent_data:
            continent = Continent()
            continent.name = continent_entry["name"]
            continent.save()

    if inject_path:
        file_path = os.path.join(inject_path, 'geographical/continents.json')
        response = requests.get(file_path)
        continent_data = json.loads(response.content)
        process_continents()
    else:
        file_path = os.path.join(os.path.dirname(module_dir), 'geographical/continents.json')
        with open(file_path) as file:
            continent_data = json.load(file)
            process_continents()


# inject region data
def inject_regions(inject_path):
    def process_regions():
        for region_entry in region_data:
            region = Region()
            region.name = region_entry["region_name"]
            region.centroid = region_entry["centroid"]
            region.polygon = ''
            coordinates = region_entry["bbox"]["coordinates"][0]
            for coordinate in coordinates:
                region.polygon += str(coordinate[0]) + "," + str(coordinate[1]) + " "
            region.save()

    if inject_path:
        file_path = os.path.join(inject_path, 'geographical/ifrc-regions.json')
        response = requests.get(file_path)
        region_data = json.loads(response.content)
        process_regions()
    else:
        file_path = os.path.join(os.path.dirname(module_dir), 'geographical/ifrc-regions.json')
        with open(file_path) as file:
            region_data = json.load(file)
            process_regions()


# inject country data
def inject_countries(inject_path):
    def process_regions():
        for region_entry in region_data:
            name = region_entry["region_name"]
            region_id = region_entry["id"]
            region_names[region_id] = name

    def process_countries_ifrc():
        for feature in country_data:
            name = feature["name"]
            region_id = feature["region"]
            iso3 = feature["iso3"]
            if ("Region" in name) or ("Cluster" in name) or (region_id is None) or (iso3 is None):
                continue
            ifrc_countries[iso3] = region_names[region_id]

    def process_countries_opendatasoft():
        for feature in country_data['features']:
            country = Country()
            country.name = feature['properties']['name']
            country.iso3 = feature['properties']['iso3']
            status = feature['properties']['status']
            if status == 'Occupied Territory (under review)' or status == 'PT Territory':
                continue
            if country.iso3 not in ifrc_countries:
                continue
            country.region = Region.objects.filter(name=ifrc_countries[country.iso3]).first()
            country.continent = Continent.objects.filter(name=feature['properties']['continent']).first()
            coordinates = feature['geometry']['coordinates']
            geometry_type = feature['geometry']['type']
            if geometry_type == 'Polygon':
                country.polygon = coordinates
            elif geometry_type == 'MultiPolygon':
                country.multipolygon = coordinates

            latitude = feature['properties']['geo_point_2d']['lat']
            longitude = feature['properties']['geo_point_2d']['lon']
            country.centroid = f'[{longitude}, {latitude}]'

            if not Country.objects.filter(iso3=country.iso3).first():
                country.save()
            processed_iso3.add(country.iso3)

    region_names = {}
    if inject_path:
        file_path = os.path.join(inject_path, 'geographical/ifrc-regions.json')
        response = requests.get(file_path)
        region_data = json.loads(response.content)
        process_regions()
    else:
        file_path = os.path.join(os.path.dirname(module_dir), 'geographical/ifrc-regions.json')
        with open(file_path) as file:
            region_data = json.load(file)
            process_regions()

    ifrc_countries = {}
    if inject_path:
        file_path = os.path.join(inject_path, 'geographical/ifrc-countries-and-territories.json')
        response = requests.get(file_path)
        country_data = json.loads(response.content)
        process_countries_ifrc()
    else:
        file_path = os.path.join(os.path.dirname(module_dir), 'geographical/ifrc-countries-and-territories.json')
        with open(file_path) as file:
            country_data = json.load(file)
            process_countries_ifrc()

    processed_iso3 = set()
    if inject_path:
        file_path = os.path.join(inject_path, 'geographical/opendatasoft-countries-and-territories.geojson')
        response = requests.get(file_path)
        country_data = json.loads(response.content)
        process_countries_opendatasoft()
    else:
        file_path = os.path.join(os.path.dirname(module_dir), 'geographical/opendatasoft-countries-and-territories.geojson')
        with open(file_path) as file:
            country_data = json.load(file)
            process_countries_opendatasoft()


# inject admin1 data
def inject_admin1s(inject_path):
    def process_admin1s():
        for feature in admin1_data['features']:
            admin1 = Admin1()
            # Skip unparsable features
            if 'shapeName' not in feature['properties']:
                continue
            admin1.name = feature['properties']['shapeName']
            iso3 = feature['properties']['shapeGroup']
            country = Country.objects.filter(iso3=iso3).first()
            # Skip ISO3 codes that do not match existing countries
            if not country:
                continue
            admin1.country = country
            coordinates = feature['geometry']['coordinates']
            geometry_type = feature['geometry']['type']
            if geometry_type == 'Polygon':
                admin1.polygon = coordinates
            elif geometry_type == 'MultiPolygon':
                admin1.multipolygon = coordinates
            admin1.save()

    if inject_path:
        file_path = os.path.join(inject_path, 'geographical/geoBoundariesCGAZ_ADM1.geojson')
        response = requests.get(file_path)
        admin1_data = json.loads(response.content)
        process_admin1s()
    else:
        file_path = os.path.join(os.path.dirname(module_dir), 'geographical/geoBoundariesCGAZ_ADM1.geojson')
        with open(file_path, encoding='utf-8') as f:
            admin1_data = json.load(f)
            process_admin1s()


# inject region and country data if not already present
def inject_geographical_data():
    inject_path = None
    if 'WEBSITE_HOSTNAME' in os.environ:
        from main.production import MEDIA_URL

        inject_path = MEDIA_URL

    if Continent.objects.count() == 0:
        print('Injecting continents...')
        inject_continents(inject_path)
    if Region.objects.count() == 0:
        print('Injecting regions...')
        inject_regions(inject_path)
    if Country.objects.count() == 0:
        print('Injecting countries...')
        inject_countries(inject_path)
        print('Injecting admin1s...')
        inject_admin1s(inject_path)
