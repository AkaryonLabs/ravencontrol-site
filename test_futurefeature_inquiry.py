import importlib.util
import unittest
from pathlib import Path

APP_PATH = Path(__file__).parent / "backend" / "app.py"
spec = importlib.util.spec_from_file_location("raven_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class FutureFeatureInquiryTests(unittest.TestCase):
    def test_normalizes_required_futurefeature_inquiry_fields(self):
        payload = {
            "owner_name": "  Akeem  ",
            "business_name": "  Clean Cuts  ",
            "business_type": " Barber  ",
            "phone": " (555) 010-2222 ",
            "email": " OWNER@EXAMPLE.COM ",
            "service_area": " Chicago ",
            "current_booking": " DMs ",
            "needs": ["website", "booking"],
            "message": " Need a page fast. ",
        }
        inquiry = app.normalize_futurefeature_inquiry(payload)
        self.assertEqual(inquiry["owner_name"], "Akeem")
        self.assertEqual(inquiry["email"], "owner@example.com")
        self.assertEqual(inquiry["needs"], ["website", "booking"])
        self.assertEqual(inquiry["status"], "New FutureFeature Starter inquiry")

    def test_futurefeature_missing_required_fields(self):
        missing = app.futurefeature_missing_required_fields({"owner_name": "Akeem"})
        self.assertIn("business_name", missing)
        self.assertIn("business_type", missing)
        self.assertIn("phone", missing)
        self.assertIn("email", missing)

    def test_futurefeature_duplicate_detects_email_or_phone(self):
        state = {
            "futurefeature_inquiries": [
                {"email": "owner@example.com", "phone": "5550102222"}
            ]
        }
        self.assertTrue(app.has_existing_futurefeature_inquiry(state, {"email": "OWNER@example.com"}))
        self.assertTrue(app.has_existing_futurefeature_inquiry(state, {"phone": "(555) 010-2222"}))
        self.assertFalse(app.has_existing_futurefeature_inquiry(state, {"email": "new@example.com", "phone": "5559990000"}))

    def test_honeypot_marks_bot_payload(self):
        self.assertTrue(app.is_futurefeature_spam({"website": "bot-filled"}))
        self.assertTrue(app.is_futurefeature_spam({"company_url": "https://spam.example"}))
        self.assertFalse(app.is_futurefeature_spam({"website": "", "company_url": ""}))


if __name__ == "__main__":
    unittest.main()
