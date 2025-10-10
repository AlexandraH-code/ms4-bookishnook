from django.test import TestCase, override_settings


@override_settings(DEBUG=False)
class Error404Tests(TestCase):
    def test_404_template_renders(self):
        res = self.client.get("/definitely-not-existing-url-xyz/")
        self.assertEqual(res.status_code, 404)
        self.assertTemplateUsed(res, "404.html")
