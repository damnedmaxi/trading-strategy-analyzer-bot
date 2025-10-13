from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AnalyticsAPITests(APITestCase):
    def test_equity_curve(self):
        url = reverse("equity-curve")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("equity_curve", response.json())

    def test_performance_summary(self):
        url = reverse("performance-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("total_return_pct", data)
