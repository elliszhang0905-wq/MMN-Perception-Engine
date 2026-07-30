import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SafeDeployScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (ROOT / "scripts" / "deploy.sh").read_text(encoding="utf-8")

    def test_build_happens_before_cutover_and_never_takes_stack_down(self):
        self.assertNotIn("compose down", self.script)
        self.assertNotIn("docker compose --env-file .env down", self.script)
        self.assertLess(
            self.script.index("compose build mmn-app"),
            self.script.index("compose up -d --no-build --remove-orphans"),
        )

    def test_running_data_is_backed_up_before_candidate_build(self):
        self.assertLess(
            self.script.index("bash scripts/backup.sh"),
            self.script.index("compose build mmn-app"),
        )
        self.assertIn("旧版本继续在线，开始构建候选镜像", self.script)

    def test_failed_cutover_has_automatic_image_rollback(self):
        self.assertIn('ROLLBACK_IMAGE_TAG="rollback"', self.script)
        self.assertIn("restore_previous_image()", self.script)
        self.assertIn(
            'docker tag "${IMAGE_REPOSITORY}:${ROLLBACK_IMAGE_TAG}" '
            '"${IMAGE_REPOSITORY}:${DEPLOY_IMAGE_TAG}"',
            self.script,
        )

    def test_deploy_has_lock_disk_gate_and_post_build_cleanup(self):
        self.assertIn("acquire_lock", self.script)
        self.assertIn("MMN_DEPLOY_MIN_FREE_MB", self.script)
        self.assertIn("docker builder prune --all --force", self.script)
        self.assertIn("MMN_DEPLOY_BUILD_TIMEOUT_SECONDS", self.script)


if __name__ == "__main__":
    unittest.main()
