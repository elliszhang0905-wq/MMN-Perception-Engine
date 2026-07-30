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
            self.script.index("compose run -d --no-deps --name"),
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

    def test_blue_green_cutover_routes_to_healthy_candidate_before_replacing_app(self):
        self.assertIn('CANDIDATE_CONTAINER_NAME="mmn-app-candidate"', self.script)
        candidate_route = self.script.index('route_web_to "$CANDIDATE_CONTAINER_NAME"')
        formal_replace = self.script.index(
            "compose up -d --no-build --no-deps --force-recreate "
            "mmn-app mmn-creator-worker mmn-scheduler",
            candidate_route,
        )
        route_back = self.script.index("route_web_to mmn-app", formal_replace)
        self.assertLess(candidate_route, formal_replace)
        self.assertLess(formal_replace, route_back)
        self.assertNotIn("compose restart mmn-app", self.script)
        self.assertNotIn("compose restart mmn-web", self.script)

    def test_cutover_updates_read_only_bind_mount_from_host_and_fails_closed(self):
        self.assertIn('NGINX_BASE_CONFIG="$(mktemp /tmp/mmn-nginx-base.', self.script)
        self.assertIn('"$NGINX_BASE_CONFIG" > "$staged_config"', self.script)
        self.assertIn('cp "$staged_config" deploy/nginx.conf', self.script)
        self.assertIn("if ! compose exec -T mmn-web nginx -t", self.script)
        self.assertNotIn("> /etc/nginx/conf.d/default.conf", self.script)

    def test_deploy_has_lock_disk_gate_and_post_build_cleanup(self):
        self.assertIn("acquire_lock", self.script)
        self.assertIn("MMN_DEPLOY_MIN_FREE_MB", self.script)
        self.assertIn("docker builder prune --all --force", self.script)
        self.assertIn("MMN_DEPLOY_BUILD_TIMEOUT_SECONDS", self.script)


if __name__ == "__main__":
    unittest.main()
