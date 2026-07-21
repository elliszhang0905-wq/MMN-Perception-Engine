import io
import json
import sqlite3
import unittest
import zipfile

import strategy_report_package as report_package


def request_body(value="事实A"):
    return {
        "scope": {
            "edition": "china", "projectId": "project-e7x", "project": "E7X上市战役",
            "brand": "AUDI", "model": "奥迪E7X",
            "timeRange": {"start": "2026-06-01", "end": "2026-06-30", "label": "2026-06-01 至 2026-06-30"},
            "tCycle": {"display": "T+49", "phaseLabel": "销售转化"},
            "cockpitVersion": "beta 1.03",
        },
        "moduleStatuses": {"nsrAndCognition": {"status": "available", "sourceType": "user_imported"}},
        "moduleData": {"productEvaluation": {"sourceType": "user_imported", "value": value}},
        "chartData": {"nsr": [{"label": "安全", "value": 0.61}]},
        "evidence": {"items": [{
            "evidenceId": "E-1", "category": "user_perception", "fact": value,
            "status": "verified", "sourceType": "user_imported", "timeRange": "2026-06",
        }]},
        "decisions": {"humanFinal": [{"statement": "先解决身份认知", "evidenceIds": ["E-1"]}]},
    }


def completed_output(statement="当前最重要的是修复身份认知"):
    return {
        "coreConclusions": [{
            "topic": "consumer_cognition", "stance": "repair", "statement": statement,
            "evidenceIds": ["E-1"],
        }],
        "primaryMarketingProblem": {"statement": "身份认知不清", "evidenceIds": ["E-1"]},
        "keyEvidence": [{"evidenceId": "E-1", "meaning": "用户表达支持该判断"}],
        "consumerCognitionImpact": {"statement": "降低价值理解", "evidenceIds": ["E-1"]},
        "competitiveImpact": {"statement": "竞品关系需要继续观察", "evidenceIds": ["E-1"]},
        "strategyJudgment": {"statement": "先修复再放大", "evidenceIds": ["E-1"]},
        "actions": {
            "stop": [{"statement": "停止无证据扩写", "evidenceIds": ["E-1"]}],
            "continue": [{"statement": "继续验证用户表达", "evidenceIds": ["E-1"]}],
            "add": [{"statement": "新增场景解释", "evidenceIds": ["E-1"]}],
        },
        "accountAndContentTasks": [{"accountRole": "专业解释型账号", "contentTask": "拆解身份关系", "evidenceIds": ["E-1"]}],
        "observableMetrics": [{"metric": "有效用户表达变化", "boundary": "不作为销量原因"}],
        "evidenceGaps": [], "unknowns": [], "pptNarrativeOrder": ["结论", "证据", "行动"],
        "citedEvidenceIds": ["E-1"],
    }


class StrategyReportPackageTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        report_package.init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def snapshot(self, body=None, org_id="org-a"):
        return report_package.create_or_reuse_snapshot(
            self.conn, body or request_body(), org_id=org_id, user_id="ellis", edition="china",
            mmn_version="beta-1.03-test", server_data={"readOnlyAdapter": True},
        )

    def test_snapshot_is_scoped_immutable_reused_and_changes_create_new_snapshot(self):
        first = self.snapshot()
        second = self.snapshot()
        changed = self.snapshot(request_body("事实B"))
        self.assertTrue(first["immutable"])
        self.assertEqual(first["orgId"], "org-a")
        self.assertEqual(first["projectId"], "project-e7x")
        self.assertEqual(first["model"], "奥迪E7X")
        self.assertEqual(first["snapshotId"], second["snapshotId"])
        self.assertTrue(second["reused"])
        self.assertNotEqual(first["snapshotId"], changed["snapshotId"])
        self.assertNotEqual(first["evidenceFingerprint"], changed["evidenceFingerprint"])

    def test_three_blind_channels_receive_identical_snapshot_and_fingerprint(self):
        snapshot = self.snapshot()
        calls = []

        def runner(role, messages):
            calls.append((role, json.loads(messages[-1]["content"]), json.dumps(messages, ensure_ascii=False)))
            return completed_output()

        package = report_package.run_package(
            self.conn, snapshot["snapshotId"], org_id="org-a", user_id="ellis", role_runner=runner,
        )
        self.assertEqual(package["status"], "completed")
        self.assertEqual(package["completedChannelCount"], 3)
        self.assertEqual(len(calls), 3)
        self.assertEqual(len({json.dumps(call[1], ensure_ascii=False, sort_keys=True) for call in calls}), 1)
        self.assertEqual({call[1]["evidenceFingerprint"] for call in calls}, {snapshot["evidenceFingerprint"]})
        self.assertTrue(all("peer" not in call[2].lower() and "其他整理" not in call[2] for call in calls))

    def test_failure_is_partial_and_never_disguised_as_three_channels(self):
        snapshot = self.snapshot()

        def runner(role, messages):
            if role == report_package.INTERNAL_ROLES[-1]:
                raise TimeoutError("通道超时")
            return completed_output()

        package = report_package.run_package(
            self.conn, snapshot["snapshotId"], org_id="org-a", user_id="ellis", role_runner=runner,
        )
        self.assertEqual(package["status"], "partial_completed")
        self.assertEqual(package["completedChannelCount"], 2)
        self.assertEqual(len(package["failedChannels"]), 1)
        _, payload = report_package.get_package_bytes(self.conn, package["packageId"], org_id="org-a")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            synthesis = json.loads(archive.read("model_synthesis.json"))
        self.assertEqual(len(synthesis["channels"]), 3)
        failed = [channel for channel in synthesis["channels"] if channel["state"] == "failed"]
        self.assertEqual(len(failed), 1)
        self.assertIn("通道超时", failed[0]["error"])

    def test_zip_contains_required_utf8_files_and_no_pptx_or_provider_names(self):
        snapshot = self.snapshot()
        package = report_package.run_package(
            self.conn, snapshot["snapshotId"], org_id="org-a", user_id="ellis",
            role_runner=lambda *_: completed_output(),
        )
        filename, payload = report_package.get_package_bytes(self.conn, package["packageId"], org_id="org-a")
        self.assertTrue(filename.startswith("MMN_策略汇报资料包_AUDI_奥迪E7X_"))
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = set(archive.namelist())
            self.assertEqual({
                "MMN_CODEX_PPT_HANDOFF.md", "cockpit_snapshot.json", "model_synthesis.json",
                "evidence_index.json", "chart_data.json", "assets/README.txt", "README.txt",
            }, names)
            self.assertFalse(any(name.endswith(".pptx") for name in names))
            handoff = archive.read("MMN_CODEX_PPT_HANDOFF.md").decode("utf-8")
            synthesis = archive.read("model_synthesis.json").decode("utf-8")
            self.assertIn("## 18. 缺失数据和未知项", handoff)
            self.assertIn("不把曝光、热度、声量、互动或情绪直接写成销量原因", handoff)
            public = (handoff + synthesis).lower()
            for provider in ("qwen", "deepseek", "kimi", "openai", "tikhub"):
                self.assertNotIn(provider, public)

    def test_cross_org_download_and_snapshot_access_are_blocked(self):
        snapshot = self.snapshot()
        package = report_package.run_package(
            self.conn, snapshot["snapshotId"], org_id="org-a", user_id="ellis",
            role_runner=lambda *_: completed_output(),
        )
        self.assertIsNone(report_package.get_snapshot(self.conn, snapshot["snapshotId"], org_id="org-b"))
        self.assertIsNone(report_package.get_package_bytes(self.conn, package["packageId"], org_id="org-b"))


if __name__ == "__main__":
    unittest.main()
