from django.test import TestCase, override_settings

"""
404 error page rendering.
"""


@override_settings(DEBUG=False)
class Error404Tests(TestCase):
    """
    Ensure 404.html is rendered when a URL is not found (production mode).
    """

    def test_404_template_renders(self):
        """
        Unknown path should return 404 and use the 404 template.
        """

        res = self.client.get("/definitely-not-existing-url-xyz/")
        self.assertEqual(res.status_code, 404)
        self.assertTemplateUsed(res, "404.html")
