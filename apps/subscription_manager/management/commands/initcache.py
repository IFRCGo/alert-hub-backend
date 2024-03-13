from django.core.management.base import BaseCommand

from main.cache import cache


class Command(BaseCommand):
    help = "This commands helps to clear cache"

    def handle(self, *args, **options):
        # import time
        all_keys = cache.keys("*")
        print(f"previous keys: {all_keys}")
        cache.clear()
        print("Clear Cache")

        # dict = {"8": {"id": 8, "event": "Marine Weather Statement", "category": "Met",
        #               "country_name": "Teyvat_1", "admin1s": ["Meng De"],
        #               "sent": "2023-08-22 21:40:59.514832+00:00"}
        #         }
        # alert_dict = {}
        # start_time = time.time()
        # for i in range(10000):
        #     list = []
        #     for j in range(200):
        #         list.append(dict)
        #     alert_dict[i] = list
        #     #cache.set("anything", list, timeout=None)
        # #print(f"time taken 1: {time.time() - start_time }")
        # cache.set("anything", alert_dict, timeout=None)
        # cache.get("anything")
        # print(f"time taken 2: {time.time() - start_time}")
