import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AllSurfacesReleaseGateTest(unittest.TestCase):
    RELEASE_VERSION = "beta-1.02-20260720-cockpit-creator-2"

    def test_all_surfaces_browser_gate_is_part_of_release_gate(self):
        release_gate = (ROOT / "scripts" / "release_gate.sh").read_text(encoding="utf-8")
        self.assertIn("scripts/release_gate_all_surfaces.js", release_gate)

    def test_all_surfaces_gate_covers_navigation_management_views_and_responsive_layout(self):
        source = (ROOT / "scripts" / "release_gate_all_surfaces.js").read_text(encoding="utf-8")
        self.assertIn('#nav button[data-page]:not([hidden])', source)
        self.assertIn('[data-group-view]', source)
        self.assertIn("1440", source)
        self.assertIn("390", source)
        self.assertIn("runtimeErrors", source)
        self.assertIn("failedResponses", source)
        self.assertIn("MMN_USERNAME", source)
        self.assertIn("#cloud-login-screen", source)

    def test_global_release_version_busts_changed_customer_assets(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn(f"style.css?v={self.RELEASE_VERSION}", index)
        self.assertIn(f"group-dashboard.css?v={self.RELEASE_VERSION}", index)
        self.assertIn(f"lead-dashboard.css?v={self.RELEASE_VERSION}", index)
        self.assertIn(f"app.js?v={self.RELEASE_VERSION}", index)
        self.assertIn(f"group-dashboard.js?v={self.RELEASE_VERSION}", index)
        self.assertIn(f"lead-dashboard.js?v={self.RELEASE_VERSION}", index)
        self.assertIn(f'APP_VERSION_CODE = "{self.RELEASE_VERSION}"', server)


if __name__ == "__main__":
    unittest.main()
