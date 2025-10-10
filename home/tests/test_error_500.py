from django.test import SimpleTestCase, override_settings
from django.urls import path
from django.views.defaults import server_error


# A small view that always crashes
def boom(request):
    raise Exception("boom")


# Minimal URLconf for this test module
urlpatterns = [
    path("boom/", boom, name="boom"),
]

# (optional) point handler500 here – Django still uses 500.html when DEBUG=False
handler500 = server_error

@override_settings(
    DEBUG=False,
    DEBUG_PROPAGATE_EXCEPTIONS=False,  # let Django handle the error and render 500.html
    ROOT_URLCONF=__name__,             # use urlpatterns above
    ALLOWED_HOSTS=["testserver"],      # so the test client doesn't get blocked
)
class Error500Tests(SimpleTestCase):
    def setUp(self):
        # Important: otherwise the test client will immediately throw the exception
        self.client.raise_request_exception = False

    def test_500_template_renders(self):
        res = self.client.get("/boom/")
        self.assertEqual(res.status_code, 500)
        self.assertTemplateUsed(res, "500.html")
