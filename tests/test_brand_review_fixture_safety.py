"""Fixture confinement tests use only fresh temporary directories."""
import base64
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('brand_browser_fixture', ROOT/'tests/fixtures/brand_review_test_server.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class FixtureSafetyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mmn-brand-review-', dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.data = self.root/'data'; self.data.mkdir()
        self.db = self.data/'commercial_demo.db'; self.db.touch()

    def test_plain_dedicated_copy_is_allowed(self):
        self.assertEqual(fixture.validate_fixture_paths(self.data, 8894), self.data)

    def test_database_symlink_is_rejected_before_write(self):
        outside = self.root/'outside.db'; outside.write_bytes(b'unchanged')
        self.db.unlink(); self.db.symlink_to(outside)
        with self.assertRaises(ValueError): fixture.validate_fixture_paths(self.data, 8894)
        self.assertEqual(outside.read_bytes(), b'unchanged')

    def test_hardlinked_database_is_rejected(self):
        os.link(self.db, self.root/'other.db')
        with self.assertRaises(ValueError): fixture.validate_fixture_paths(self.data, 8894)

    def test_symlinked_runtime_output_is_rejected(self):
        outside = self.root/'outside'; outside.mkdir()
        (self.root/'output').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): fixture.validate_fixture_paths(self.data, 8894)

    def test_production_port_is_rejected(self):
        with self.assertRaises(ValueError): fixture.validate_fixture_paths(self.data, 8765)

    def test_fixture_accepts_policy_sorted_competitors(self):
        import brand_review_policy as policy
        from tests.test_brand_review_policy import SCOPE, WINDOW
        packet = policy.build_layered_packet({'keyword':fixture.BRANDS[0],
            'modelComparisons':[{'model':b,'role':'own' if i==0 else 'competitor'}
                for i,b in enumerate(fixture.BRANDS)]}, SCOPE, WINDOW)
        fixture.validate_synthetic_packet(packet)
        with self.assertRaises(ValueError):
            fixture.validate_synthetic_packet({**packet,'ownBrand':'非合成品牌'})

    def test_brand_inline_script_matches_exact_csp_hash(self):
        html = (ROOT/'demo-brand-weekly-radar.html').read_text()
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', html, flags=re.S|re.I)
        self.assertEqual(len(scripts), 1)
        digest = base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode()
        server = (ROOT/'server.py').read_text()
        self.assertTrue("'sha256-"+digest+"'" in server, 'Brand script blocked by stale CSP hash')


if __name__ == '__main__': unittest.main()
