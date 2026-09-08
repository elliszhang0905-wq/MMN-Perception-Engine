"""Execute a copied deploy script with fake Docker; never access a daemon."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

# Every command is logged. Only the explicit harmless fake responses exist.
DOCKER = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['DEPLOY_TEST_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\n')
if args[:1] == ['compose']:
    args = args[3:]  # --env-file .env
    if args[:1] == ['ps'] and '--services' in args:
        print('mmn-app')
    if args[:1] == ['build'] and os.environ.get('DEPLOY_TEST_FAIL_BUILD') == '1':
        sys.exit(19)
    if args[:1] == ['up'] and os.environ.get('DEPLOY_TEST_FAIL_CUTOVER') == '1':
        marker = Path(os.environ['DEPLOY_TEST_LOG'] + '.failed-once')
        if not marker.exists():
            marker.touch()
            sys.exit(20)
    if args[:5] == ['exec', '-T', 'mmn-web', 'nginx', '-t'] and os.environ.get('DEPLOY_TEST_FAIL_ROUTE') == '1':
        if 'mmn-app-candidate:8765' in Path('deploy/nginx-runtime/default.conf').read_text():
            sys.exit(25)
elif args[:1] == ['tag'] and args[-1] == 'test-mmn:latest':
    if os.environ.get('DEPLOY_TEST_FAIL_PROMOTE') == '1' and ':candidate-' in args[1]:
        sys.exit(26)
    Path(os.environ['DEPLOY_TEST_LOG'] + '.formal-tag').write_text(args[1])
elif args[:1] == ['inspect']:
    fmt = args[2]
    failed_stage = os.environ.get('DEPLOY_TEST_FAIL_HEALTH')
    restarted = Path(os.environ['DEPLOY_TEST_LOG'] + '.restarted').exists()
    if args[-1] == 'mmn-app-candidate' and '.Health' in fmt and (failed_stage == 'first' or (failed_stage == 'second' and restarted)):
        print('unhealthy')
        sys.exit(0)
    print('123456789' if '.Pid' in fmt else 'previous-image-id' if '.Image' in fmt else 'healthy')
elif args[:2] == ['restart', 'mmn-app-candidate']:
    Path(os.environ['DEPLOY_TEST_LOG'] + '.restarted').touch()
elif args[:1] == ['top']:
    print('PID PPID COMMAND')
'''


class CodeOnlyDeployTest(unittest.TestCase):
    def run_deploy(self, *, mode='true', fail_build=False, fail_cutover=False, env_mode=None,
                   fail_health='', fail_route=False, fail_promote=False):
        with tempfile.TemporaryDirectory(prefix='mmn-brand-deploy-test-') as raw:
            root = Path(raw)
            for name in ('scripts', 'deploy', 'bin', 'data'):
                (root / name).mkdir()
            shutil.copy2(ROOT / 'scripts/deploy.sh', root / 'scripts/deploy.sh')
            (root / 'deploy/nginx.conf').write_text('proxy_pass http://mmn-app:8765;\n')
            (root / '.env').write_text('MMN_IMAGE_REPOSITORY=test-mmn\n' + (
                f'MMN_DEPLOY_CODE_ONLY={env_mode}\n' if env_mode is not None else ''))
            (root / 'scripts/backup.sh').write_text(
                '#!/usr/bin/env bash\nprintf \'["backup"]\\n\' >> "$DEPLOY_TEST_LOG"\n')
            (root / 'data/thailand_social_market_latest.json').write_text('{"unchanged":true}\n')
            (root / 'data/commercial_demo.db').write_bytes(b'not-a-real-database')
            before = {p.name: p.read_bytes() for p in (root / 'data').iterdir()}
            (root / 'bin/docker').write_text(DOCKER.replace('#!/usr/bin/env python3', '#!' + sys.executable, 1))
            (root / 'bin/docker').chmod(0o700)
            (root / 'bin/sleep').write_text('#!/bin/sh\nexit 0\n')
            (root / 'bin/sleep').chmod(0o700)
            log = root / 'calls.jsonl'
            Path(str(log) + '.formal-tag').write_text('previous-image-id')
            env = {'PATH': f'{root / "bin"}:/usr/bin:/bin:/usr/sbin:/sbin',
                   'MMN_SKIP_GIT_PULL': 'true', 'MMN_DEPLOY_MIN_FREE_MB': '0',
                   'DEPLOY_TEST_LOG': str(log), 'DEPLOY_TEST_FAIL_BUILD': str(int(fail_build)),
                   'DEPLOY_TEST_FAIL_CUTOVER': str(int(fail_cutover)),
                   'DEPLOY_TEST_FAIL_HEALTH': fail_health,
                   'DEPLOY_TEST_FAIL_ROUTE': str(int(fail_route)),
                   'DEPLOY_TEST_FAIL_PROMOTE': str(int(fail_promote))}
            if mode is not None:
                env['MMN_DEPLOY_CODE_ONLY'] = mode
            resolved = subprocess.run(['bash', '-c', 'command -v docker'], cwd=root,
                                      env=env, capture_output=True, text=True, check=True)
            self.assertEqual(Path(resolved.stdout.strip()), root / 'bin/docker')
            process = subprocess.run(['bash', 'scripts/deploy.sh'], cwd=root, env=env,
                                     capture_output=True, text=True, timeout=40)
            calls = [json.loads(s) for s in log.read_text().splitlines()] if log.exists() else []
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root / 'data').iterdir()})
            process.formal_image = Path(str(log) + '.formal-tag').read_text()
            return process, calls

    @staticmethod
    def compose_calls(calls, command):
        return [c[3:] for c in calls if c[:3] == ['compose', '--env-file', '.env'] and c[3:4] == [command]]

    def test_code_only_skips_data_sync_and_unrelated_service_restart(self):
        process, calls = self.run_deploy()
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.assertEqual(self.compose_calls(calls, 'cp'), [])
        self.assertFalse(any('/app/data' in ' '.join(c) for c in calls))
        up = self.compose_calls(calls, 'up')
        self.assertEqual(len(up), 1)
        self.assertEqual(up[0], ['up', '-d', '--no-build', '--no-deps', '--force-recreate', 'mmn-app'])
        self.assertIn(['backup'], calls)
        self.assertFalse(any('down' in c or '-v' in c for c in calls))

    def test_default_mode_preserves_release_asset_and_service_contract(self):
        process, calls = self.run_deploy(mode=None)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(any('data/thailand_social_market_latest.json' in c for c in self.compose_calls(calls, 'cp')))
        self.assertEqual(self.compose_calls(calls, 'up')[0][-3:], ['mmn-app', 'mmn-creator-worker', 'mmn-scheduler'])

    def test_explicit_code_only_cannot_be_overridden_by_dotenv(self):
        process, calls = self.run_deploy(env_mode='false')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(self.compose_calls(calls, 'cp'), [])

    def test_dotenv_alone_cannot_enable_code_only(self):
        process, calls = self.run_deploy(mode=None, env_mode='true')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(self.compose_calls(calls, 'cp'))
        self.assertEqual(self.compose_calls(calls, 'up')[0][-3:],
                         ['mmn-app', 'mmn-creator-worker', 'mmn-scheduler'])

    def test_invalid_mode_stops_before_docker(self):
        process, calls = self.run_deploy(mode='tru')
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(calls, [])

    def test_build_failure_never_stops_or_switches_old_app(self):
        process, calls = self.run_deploy(fail_build=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(self.compose_calls(calls, 'up'), [])
        self.assertEqual(self.compose_calls(calls, 'run'), [])
        self.assertFalse(any(c[:1] in (['stop'], ['rm']) or 'down' in c for c in calls))

    def test_archive_cutover_failure_uses_image_rollback_without_data_restore(self):
        process, calls = self.run_deploy(fail_cutover=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn(['tag', 'previous-image-id', 'test-mmn:rollback'], calls)
        self.assertIn(['tag', 'test-mmn:rollback', 'test-mmn:latest'], calls)
        self.assertEqual(len(self.compose_calls(calls, 'up')), 2)
        self.assertTrue(all(c[-1] == 'mmn-app' and 'mmn-creator-worker' not in c for c in self.compose_calls(calls, 'up')))
        self.assertFalse(any('restore' in ' '.join(c) or 'down' in c for c in calls))

    def test_rejected_candidate_never_retags_formal_image(self):
        for failure in ({'fail_health':'first'}, {'fail_health':'second'}, {'fail_route':True}):
            with self.subTest(failure=failure):
                process, calls = self.run_deploy(**failure)
                self.assertNotEqual(process.returncode, 0)
                self.assertEqual(self.compose_calls(calls, 'up'), [])
                self.assertFalse(any(c[:1] == ['tag'] and c[-1] == 'test-mmn:latest' for c in calls))

    def test_candidate_tag_promoted_only_after_route_acceptance(self):
        process, calls = self.run_deploy()
        self.assertEqual(process.returncode, 0)
        promote = next(i for i,c in enumerate(calls) if c[:1] == ['tag'] and c[-1] == 'test-mmn:latest')
        health = next(i for i,c in enumerate(calls) if 'http://mmn-app-candidate:8765/api/health' in c)
        recreate = next(i for i,c in enumerate(calls) if c[:4] == ['compose','--env-file','.env','up'])
        self.assertLess(health, promote)
        self.assertLess(promote, recreate)

    def test_failed_tag_promotion_restores_old_route_without_recreating(self):
        process, calls = self.run_deploy(fail_promote=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(process.formal_image, 'previous-image-id')
        self.assertEqual(self.compose_calls(calls, 'up'), [])
        promote = next(i for i,c in enumerate(calls) if c[:1] == ['tag'] and c[-1] == 'test-mmn:latest')
        self.assertTrue(any('http://mmn-app:8765/api/health' in c for c in calls[promote+1:]))
        self.assertIn(['rm', 'mmn-app-candidate'], calls[promote+1:])


if __name__ == '__main__':
    unittest.main()
