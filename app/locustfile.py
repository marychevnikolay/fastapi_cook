from locust import HttpUser, task


class User(HttpUser):

    @task
    def get_posts(self):
        self.client.get("/posts")
