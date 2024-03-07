import os
import json
from locust import HttpUser, task, between
import csv


# class SubscriptionUser(HttpUser):
#     host = "http://127.0.0.1:8000"
#     wait_time = between(0, 1)
#
#     @task
#     def read_csv_and_send_requests(self):
#         with open(os.path.join(os.path.dirname(__file__), 'fake_users.csv'), 'r') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 subscription_ids = json.loads(row['subscription_ids'])
#                 for subscription_id in subscription_ids:
#                     url = f"/subscription_manager/get_subscription_alerts/{subscription_id}/"
#                     self.client.get(url)

class SubscriptionUser(HttpUser):
    wait_time = between(0, 1)

    @task
    def send_requests(self):
        url = f"/subscription_manager/get_subscription_alerts/3484/"

        # url = f"/subscription_manager/get_subscription_alerts_in_real_time/6/"
        self.client.get(url)
