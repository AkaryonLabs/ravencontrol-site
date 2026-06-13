import importlib.util
import unittest
from pathlib import Path

APP_PATH = Path(__file__).parent / "backend" / "app.py"
spec = importlib.util.spec_from_file_location("raven_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class AppTierTests(unittest.TestCase):
    def test_free_plan_unlocks_only_satacheck(self):
        access = app.tier_access_for_plan("free")
        self.assertTrue(access["satacheck"])
        self.assertFalse(access["circle"])
        self.assertFalse(access["companion"])
        self.assertFalse(access["business"])
        self.assertFalse(access["vault"])

    def test_family_plan_unlocks_circle_and_vault(self):
        access = app.tier_access_for_plan("circle")
        self.assertTrue(access["satacheck"])
        self.assertTrue(access["circle"])
        self.assertTrue(access["vault"])
        self.assertFalse(access["business"])

    def test_business_plan_unlocks_business_and_vault(self):
        access = app.tier_access_for_plan("business")
        self.assertTrue(access["satacheck"])
        self.assertTrue(access["business"])
        self.assertTrue(access["vault"])
        self.assertFalse(access["circle"])

    def test_companion_plan_unlocks_human_guidance(self):
        access = app.tier_access_for_plan("companion")
        self.assertTrue(access["satacheck"])
        self.assertTrue(access["companion"])
        self.assertTrue(access["vault"])


if __name__ == "__main__":
    unittest.main()
