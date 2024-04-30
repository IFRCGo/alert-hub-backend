import json
import logging
import os

from apps.cap_feed.models import Country, Feed, LanguageInfo

module_dir = os.path.dirname(__file__)  # get current directory
logger = logging.getLogger(__name__)


# inject feed configurations if not already present
def inject_feeds():
    file_path = os.path.join(
        os.path.dirname(module_dir),
        'feeds.json',
    )
    with open(file_path, encoding='utf-8') as file:
        feeds = json.load(file)
        logger.info('Injecting feeds...')
        unique_countries = set()
        feed_counter = 0
        for feed_entry in feeds:
            try:
                feed = Feed()
                feed.url = feed_entry['capAlertFeed']
                feed.country = Country.objects.get(iso3=feed_entry['iso3'])
                feed_counter += 1
                unique_countries.add(feed_entry['iso3'])
                if Feed.objects.filter(url=feed.url).first():
                    continue
                feed.format = feed_entry['format']
                feed.polling_interval = Feed.PoolingInterval.I_10m
                feed.enable_polling = True
                feed.enable_rebroadcast = True
                feed.official = True
                feed.save()

                language_info = LanguageInfo()
                language_info.feed = feed
                language_info.name = feed_entry['name']
                language_info.language = feed_entry['language']
                language_info.logo = feed_entry['picUrl']
                language_info.save()

            except Exception:
                logger.error(f"Error injecting feed: {feed_entry['name']}", exc_info=True)

        logger.info(f'Injected {feed_counter} feeds for {len(unique_countries)} unique countries')
