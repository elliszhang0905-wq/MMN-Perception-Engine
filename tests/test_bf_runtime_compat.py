import shutil
import subprocess
import unittest


class BFRuntimeCompatibilityTest(unittest.TestCase):
    def test_system_python_can_import_server_without_optional_document_packages(self):
        python = shutil.which("python3")
        self.assertIsNotNone(python)
        process = subprocess.run(
            [python, "-c", "import server; print('server-import-ok')"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("server-import-ok", process.stdout)


if __name__ == "__main__":
    unittest.main()
