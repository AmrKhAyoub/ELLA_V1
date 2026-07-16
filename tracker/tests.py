from django.test import TestCase
from django.urls import reverse


class UpdateLocationAPITests(TestCase):
    def test_options_preflight_is_allowed(self):
        response = self.client.options(
            reverse("update_location"),
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("http://localhost:3000", response["Access-Control-Allow-Origin"])
        self.assertIn("POST", response["Access-Control-Allow-Methods"])

    def test_post_location_is_accepted_from_browser_origin(self):
        response = self.client.post(
            reverse("update_location"),
            data={"latitude": 40.7128, "longitude": -74.0060},
            content_type="application/json",
            HTTP_ORIGIN="http://localhost:3000",
        )

        self.assertEqual(response.status_code, 202)
        self.assertIn("http://localhost:3000", response["Access-Control-Allow-Origin"])
