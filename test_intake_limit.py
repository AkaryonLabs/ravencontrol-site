import importlib.util
import unittest
from pathlib import Path

APP_PATH = Path(__file__).parent / "backend" / "app.py"
spec = importlib.util.spec_from_file_location("raven_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class IntakeLimitTests(unittest.TestCase):
    def test_email_customer_key_is_case_insensitive_and_trimmed(self):
        payload = {"email": "  Person@Example.COM  ", "phone": "(555) 111-2222"}
        self.assertEqual(app.customer_limit_key(payload), "email:person@example.com")

    def test_phone_customer_key_normalizes_digits_when_email_missing(self):
        payload = {"phone": "(555) 111-2222"}
        self.assertEqual(app.customer_limit_key(payload), "phone:5551112222")

    def test_has_used_free_intake_matches_existing_case_by_email(self):
        state = {
            "cases": [
                {
                    "offer": "website_intake",
                    "contact": {"email": "person@example.com", "phone": ""},
                }
            ]
        }
        payload = {"email": " Person@Example.com "}
        self.assertTrue(app.has_used_free_intake(state, payload))

    def test_has_used_free_intake_matches_current_free_offer_name(self):
        state = {
            "cases": [
                {
                    "offer": "free_one_time_scam_check",
                    "contact": {"email": "person@example.com", "phone": ""},
                }
            ]
        }
        payload = {"email": "person@example.com"}
        self.assertTrue(app.has_used_free_intake(state, payload))

    def test_has_used_free_intake_ignores_guardian_cases_without_public_offer(self):
        state = {
            "cases": [
                {
                    "offer": "guardian_review",
                    "contact": {"email": "person@example.com", "phone": "5551112222"},
                }
            ]
        }
        payload = {"email": "person@example.com"}
        self.assertFalse(app.has_used_free_intake(state, payload))


if __name__ == "__main__":
    unittest.main()
