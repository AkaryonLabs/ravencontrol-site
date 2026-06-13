import importlib.util
import unittest
from pathlib import Path

APP_PATH = Path(__file__).parent / "backend" / "app.py"
spec = importlib.util.spec_from_file_location("raven_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class AppRouteTests(unittest.TestCase):
    def test_app_routes_include_dashboard_aliases(self):
        self.assertIn("/app", app.APP_ROUTES)
        self.assertIn("/app/", app.APP_ROUTES)
        self.assertIn("/app/index.html", app.APP_ROUTES)

    def test_app_page_route_maps_tier_pages(self):
        self.assertEqual(app.app_page_for_path("/app/satacheck.html"), "satacheck.html")
        self.assertEqual(app.app_page_for_path("/app/circle.html"), "circle.html")
        self.assertEqual(app.app_page_for_path("/app/business.html"), "business.html")
        self.assertEqual(app.app_page_for_path("/app/companion.html"), "companion.html")
        self.assertEqual(app.app_page_for_path("/app/vault.html"), "vault.html")

    def test_app_page_route_rejects_path_traversal(self):
        self.assertIsNone(app.app_page_for_path("/app/../backend/app.py"))
        self.assertIsNone(app.app_page_for_path("/app/not-real.html"))


if __name__ == "__main__":
    unittest.main()
