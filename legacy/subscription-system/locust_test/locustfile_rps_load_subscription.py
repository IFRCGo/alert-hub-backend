from locust import HttpUser, task, between

class MySubscription(HttpUser):
    wait_time = between(0, 0)

    @task
    def test_list_subscription(self):
        query = """
            query read {
              listSubscription(
                admin1Ids: [1000001]
                certaintyArray: ["unknown"]
                countryIds: []
                severityArray: ["unknown"]
                urgencyArray: ["unknown"]
              ) {
                admin1Ids
                certaintyArray
                id
                countryIds
                sentFlag
                severityArray
                subscribeBy
                urgencyArray
                subscriptionName
                userId
              }
            }
        """
        self.client.post("/subscription/graphql",
                         json={'query': query},
                         headers={'Content-Type': 'application/json'})
