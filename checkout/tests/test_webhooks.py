from django.test import TestCase, Client
from django.urls import reverse
import json


class WebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("checkout:webhook")  # byt till din webhook-url name

    def test_webhook_dev_mode_no_signature(self):
        # Dev-läge: om din vy har specialfall utan signatur
        payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_123"}}}
        resp = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        # 200 eller 204 beroende på din vy
        self.assertIn(resp.status_code, (200, 204))
