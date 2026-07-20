import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class DataGovernanceTest(unittest.TestCase):
    def test_module_path_prefers_canonical_and_only_falls_back_for_reads(self):
        with tempfile.TemporaryDirectory() as temporary:
            import mmn_data
            with patch.object(mmn_data, "DATA_ROOT", Path(temporary)):
                legacy = Path(temporary) / "legacy.json"
                legacy.write_text("{}", encoding="utf-8")
                self.assertEqual(mmn_data.module_path("product_evaluation", "asset.json", legacy=("legacy.json",)), legacy)
                canonical = mmn_data.module_path("product_evaluation", "asset.json", legacy=("legacy.json",), for_write=True)
                self.assertEqual(canonical, Path(temporary) / "modules" / "product_evaluation" / "asset.json")
                self.assertTrue(canonical.parent.is_dir())

    def test_unknown_module_cannot_write_to_data_root(self):
        import mmn_data

        with self.assertRaises(KeyError):
            mmn_data.module_path("unknown", "asset.json", for_write=True)

    def test_backup_scripts_emit_checksums_and_server_copy(self):
        root = Path(__file__).resolve().parents[1]
        local_script = (root / "scripts" / "backup_local_data.sh").read_text(encoding="utf-8")
        server_script = (root / "scripts" / "backup.sh").read_text(encoding="utf-8")
        self.assertIn("MMN_DATA_ROOT", local_script)
        self.assertIn("manifest.sha256", local_script)
        self.assertIn("manifest.sha256", server_script)
        self.assertIn("/app/backups", server_script)


if __name__ == "__main__":
    unittest.main()
