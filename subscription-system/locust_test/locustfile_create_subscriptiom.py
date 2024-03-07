from locust import HttpUser, task, between


class MySubscription(HttpUser):
    wait_time = between(1, 2)

    @task
    def test_list_subscription(self):
        query = """
            mutation{
                createSubscriptionTest(
                    userId:1, 
                    admin1Ids:[-161],
                    certaintyArray:["Observed", "Likely", "Possible"],
  	                countryIds:[161],
  	                sentFlag:0,
  	                severityArray:["Severe"],
  	                urgencyArray:["Immediate"],
  	                subscriptionName:"1234",
  	                subscribeBy:"1234") 
  	                {
                        subscription{
                            id
                        }
                    }
            }
        """
        self.client.post("/subscription/graphql",
                         json={'query': query},
                         headers={'Content-Type': 'application/json'})
