from django.test import SimpleTestCase, override_settings
from django.urls import path
from django.views.defaults import server_error

"""
500 error page rendering with a minimal URLConf for the test.
"""


def boom(request):
    """
    A tiny view that always raises to trigger a 500.
    """

    raise Exception("boom")


urlpatterns = [
    path("boom/", boom, name="boom"),
]

handler500 = server_error


@override_settings(
    DEBUG=False,
    DEBUG_PROPAGATE_EXCEPTIONS=False,
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["testserver"],   
)
class Error500Tests(SimpleTestCase):
    """
    Ensure 500.html is rendered on unhandled exceptions.
    """

    def setUp(self):
        """
        Disable raising exceptions to the test client so the template can render.
        """

        self.client.raise_request_exception = False

    def test_500_template_renders(self):
        """
        Crashing view should return 500 and use the 500 template.
        """

        res = self.client.get("/boom/")
        self.assertEqual(res.status_code, 500)
        self.assertTemplateUsed(res, "500.html")
