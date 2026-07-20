import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from douyin_browser_evidence import BrowserEvidenceError, extract_browser_video_evidence


class DouyinBrowserEvidenceTest(unittest.TestCase):
    def test_rejects_non_douyin_and_mismatched_item_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(BrowserEvidenceError):
                extract_browser_video_evidence("https://example.com/video/1", "1", Path(tmp))
            with self.assertRaises(BrowserEvidenceError):
                extract_browser_video_evidence("https://www.douyin.com/video/123", "456", Path(tmp))

    def test_returns_only_existing_timestamped_browser_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = root / "frame-00000.jpg"
            frame.write_bytes(b"actual-frame")
            payload = {
                "pageAvailable": True,
                "mediaAvailable": True,
                "durationMs": 223000,
                "frames": [{"path": str(frame), "timestampMs": 0}],
                "mediaFingerprint": "browser-fingerprint",
            }
            completed = subprocess.CompletedProcess([], 0, json.dumps(payload, ensure_ascii=False), "")
            with patch("douyin_browser_evidence.subprocess.run", return_value=completed) as runner:
                result = extract_browser_video_evidence(
                    "https://www.douyin.com/video/123", "123", root,
                    cdp_url="http://127.0.0.1:9225", node_binary="node",
                    script_path=root / "worker.js",
                    node_modules=root / "node_modules",
                    browser_executable="/usr/bin/chromium",
                )
            self.assertEqual(result["imagePaths"], [str(frame.resolve())])
            self.assertEqual(result["timestampsMs"], [0])
            self.assertTrue(result["mediaAvailable"])
            command = runner.call_args.args[0]
            environment = runner.call_args.kwargs["env"]
            self.assertNotIn("shell=True", command)
            self.assertEqual(command[-3:], ["https://www.douyin.com/video/123", "123", str(root.resolve())])
            self.assertEqual(environment["NODE_PATH"], str((root / "node_modules").resolve()))
            self.assertEqual(environment["MMN_DOUYIN_BROWSER_EXECUTABLE"], "/usr/bin/chromium")

    def test_worker_has_server_headless_fallback_without_hiding_evidence_failure(self):
        worker = Path(__file__).resolve().parents[1] / "scripts" / "douyin_video_browser_evidence.js"
        source = worker.read_text(encoding="utf-8")
        self.assertIn("chromium.connectOverCDP", source)
        self.assertIn("chromium.launch", source)
        self.assertIn("MMN_DOUYIN_BROWSER_EXECUTABLE", source)
        self.assertIn('throw new Error("no playable video body")', source)

    def test_plugin_or_worker_error_never_becomes_empty_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            failed = subprocess.CompletedProcess([], 1, "", "browser could not read video")
            with patch("douyin_browser_evidence.subprocess.run", return_value=failed):
                with self.assertRaisesRegex(BrowserEvidenceError, "浏览器未能读取视频本体"):
                    extract_browser_video_evidence(
                        "https://www.douyin.com/video/123", "123", Path(tmp),
                        node_binary="node", script_path=Path(tmp) / "worker.js",
                    )


if __name__ == "__main__":
    unittest.main()
