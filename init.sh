#!/bin/bash

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $BASE_DIR

# Download static files
cd $BASE_DIR/apps/cap_feed/geographical
wget --no-clobber https://capaggregator.blob.core.windows.net/media/geographical/continents.json
wget --no-clobber https://capaggregator.blob.core.windows.net/media/geographical/ifrc-regions.json
wget --no-clobber https://capaggregator.blob.core.windows.net/media/geographical/ifrc-regions.json
wget --no-clobber https://capaggregator.blob.core.windows.net/media/geographical/ifrc-countries-and-territories.json
wget --no-clobber https://capaggregator.blob.core.windows.net/media/geographical/opendatasoft-countries-and-territories.geojson
wget --no-clobber https://capaggregator.blob.core.windows.net/media/geographical/geoBoundariesCGAZ_ADM1.geojson

cd $BASE_DIR
# TODO: Start a initial inject script


# TODO: Setup celery schedular
