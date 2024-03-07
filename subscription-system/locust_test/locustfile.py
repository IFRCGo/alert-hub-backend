from locust import HttpUser, task, between
import faker

class MyUser(HttpUser):
    wait_time = between(0, 1)

    @task
    def send_email(self):
        fake = faker.Faker()
        email = fake.email()
        query = """
        mutation {
            sendVerifyEmail(email: "%s") {
                success
            }
        }
        """ % email
        self.client.post("users/graphql", json={'query': query}, headers={'Content-Type':
                                                                          'application/json'})
