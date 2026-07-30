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
        self.assertLess(
            self.script.index('docker tag "$PREVIOUS_IMAGE_ID"'),
            self.script.rindex("ensure_build_capacity"),
        )
        self.assertIn("docker image prune --force", self.script)

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

    def test_nginx_route_switch_updates_read_only_bind_source_then_reloads(self):
        self.assertIn(
            'cp "$routed_config" deploy/nginx-runtime/default.conf', self.script
        )
        self.assertIn("compose exec -T mmn-web nginx -s reload", self.script)
        self.assertNotIn("> /etc/nginx/conf.d/default.conf", self.script)
        compose_config = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn(
            "./deploy/nginx-runtime:/etc/nginx/conf.d:ro", compose_config
        )
        self.assertNotIn(
            "./deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro",
            compose_config,
        )

    def test_deploy_has_lock_disk_gate_and_post_build_cleanup(self):
        self.assertIn("acquire_lock", self.script)
        self.assertIn("MMN_DEPLOY_MIN_FREE_MB", self.script)
        self.assertIn("docker builder prune --all --force", self.script)
        self.assertIn("MMN_DEPLOY_BUILD_TIMEOUT_SECONDS", self.script)


if __name__ == "__main__":
    unittest.main()
