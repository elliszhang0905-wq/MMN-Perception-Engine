import io
import sqlite3
import unittest
import zipfile

import vehicle_decision as vd


def surface_inputs(*, conflict=False, only_two=False):
    populated = {
        "executive_summary": [{"conclusion": "E7X当前线索充足但订单承接偏弱", "claimType": "inference", "evidenceIds": ["E-exec-1"], "timeWindow": "2026-06-16/2026-06-30", "businessImpact": 5, "confidence": 0.78}],
        "group_impact": [{"conclusion": "集团新能源SUV结构需要补强", "claimType": "inference", "evidenceIds": ["E-group-1"], "timeWindow": "2026-06", "businessImpact": 4, "confidence": 0.72}],
        "sales_warning": [{"conclusion": "销量承接风险高", "claimType": "fact", "evidenceIds": ["E-sales-1"], "timeWindow": "2026-06", "businessImpact": 5, "confidence": 0.91, "metricDefinition": "全国月销量"}],
        "track_environment": [{"conclusion": "纯电SUV赛道竞争加剧", "claimType": "inference", "evidenceIds": ["E-track-1"], "timeWindow": "2026-06", "businessImpact": 4, "confidence": 0.75}],
        "policy_environment": [{"conclusion": "当前政策与E7X适配需人工确认", "claimType": "unknown", "evidenceIds": [], "timeWindow": "2026-07", "businessImpact": 3, "confidence": 0.2}],
        "communication_momentum": [{"conclusion": "传播势能走弱", "claimType": "inference", "evidenceIds": ["E-social-1"], "timeWindow": "2026-06", "businessImpact": 4, "confidence": 0.7}],
        "platform_position": [{"conclusion": "垂媒对比占位不足", "claimType": "fact", "evidenceIds": ["E-platform-1"], "timeWindow": "2026-W26", "businessImpact": 4, "confidence": 0.84}],
        "product_voice": [{"conclusion": "用户产品认知正向" if conflict else "用户对智驾边界仍有疑问", "claimType": "inference", "evidenceIds": ["E-voc-1"], "timeWindow": "2026-06", "businessImpact": 4, "confidence": 0.76}],
    }
    if only_two:
        return {key: populated[key] for key in ("sales_warning", "product_voice")}
    return populated


class VehicleDecisionTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        vd.init_vehicle_decision_schema(self.conn)
        self.scope = {"org_id": "org-a", "user_id": "ellis", "edition": "china"}

    def tearDown(self):
        self.conn.close()

    def snapshot(self, **extra):
        payload = {
            "brand": "AUDI",
            "model": "AUDI E7X",
            "project": "E7X上市复盘",
            "vehicleStage": "上市期",
            "businessQuestion": "如何提高订单承接",
            "coreCompetitors": ["Model Y", "小米YU7"],
            "dataCutoffAt": "2026-07-21T08:00:00Z",
            "surfaceInputs": surface_inputs(**extra),
        }
        return vd.create_snapshot(self.conn, payload, **self.scope)

    def test_snapshot_freezes_eight_surfaces_and_fingerprint(self):
        snapshot = self.snapshot()
        self.assertEqual(len(snapshot["surfaceCoverage"]), 8)
        self.assertEqual(len(snapshot["signals"]), 8)
        self.assertTrue(snapshot["dataFingerprint"])
        self.assertEqual(snapshot["model"], "AUDI E7X")
        self.assertTrue(all(signal["snapshotId"] == snapshot["id"] for signal in snapshot["signals"]))
        self.assertEqual({signal["claimType"] for signal in snapshot["signals"]} & {"fact", "inference", "hypothesis", "unknown"}, {signal["claimType"] for signal in snapshot["signals"]})

    def test_missing_surfaces_are_explicit_and_never_fabricated(self):
        snapshot = self.snapshot(only_two=True)
        coverage = {item["surface"]: item["evidenceStatus"] for item in snapshot["surfaceCoverage"]}
        self.assertEqual(sum(status != "missing" for status in coverage.values()), 2)
        self.assertEqual(len(snapshot["signals"]), 8)
        missing = [item for item in snapshot["signals"] if item["evidenceStatus"] == "missing"]
        self.assertEqual(len(missing), 6)
        self.assertTrue(all(item["claimType"] == "unknown" and not item["evidenceIds"] for item in missing))

    def test_report_versions_are_immutable_and_conflicts_require_manual_review(self):
        snapshot = self.snapshot(conflict=True)
        first = vd.generate_report(self.conn, snapshot["id"], org_id="org-a", user_id="ellis")
        second = vd.generate_report(self.conn, snapshot["id"], org_id="org-a", user_id="ellis")
        self.assertEqual([first["version"], second["version"]], [1, 2])
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(first["status"], "manual_required")
        self.assertTrue(first["conflicts"])
        versions = vd.list_report_versions(self.conn, snapshot["id"], org_id="org-a")
        self.assertEqual([item["version"] for item in versions], [2, 1])
        self.assertEqual(versions[-1]["content"], first["content"])

    def test_action_result_learning_and_knowhow_gates(self):
        snapshot = self.snapshot()
        report = vd.generate_report(self.conn, snapshot["id"], org_id="org-a", user_id="ellis")
        decision_id = report["content"]["topDecisions"][0]["signalId"]
        with self.assertRaisesRegex(ValueError, "人工批准"):
            vd.create_action(self.conn, {"reportId": report["id"], "decisionId": decision_id}, **self.scope)

        vd.publish_report(self.conn, report["id"], org_id="org-a", user_id="ellis", approval_note="隔离测试批准")
        action = vd.create_action(self.conn, {
            "reportId": report["id"], "decisionId": decision_id, "hypothesis": "补强订单承接说明可提升询价质量",
            "owner": "测试负责人", "target": "隔离测试人群", "platform": "测试平台", "region": "上海",
            "audience": "隔离样本", "startAt": "2026-06-16", "endAt": "2026-06-30",
            "baseline": {"qualifiedLeadRate": 0.18}, "targetValue": {"qualifiedLeadRate": 0.22},
            "leadingIndicator": "有效评论质量", "resultIndicator": "有效询价", "stopCondition": "负面反馈连续两周上升",
        }, **self.scope)
        self.assertEqual(action["status"], "approved")
        vd.update_action_status(self.conn, action["id"], "running", org_id="org-a", user_id="ellis")
        vd.update_action_status(self.conn, action["id"], "observed", org_id="org-a", user_id="ellis")
        result = vd.record_result(self.conn, action["id"], {
            "metrics": {"volume": 0, "interaction": None, "qualifiedComments": 12, "leads": 8, "orders": None},
            "actualExecution": "完成隔离测试内容", "completionRate": 1, "actualTimeWindow": "2026-06-16/2026-06-30",
            "externalVariables": ["同期价格不变"], "observation": "有效询价增加", "evidenceIds": ["E-result-1"]
        }, org_id="org-a", user_id="ellis")
        self.assertEqual(result["metrics"]["volume"], 0)
        self.assertIsNone(result["metrics"]["interaction"])
        self.assertIsNone(result["metrics"]["orders"])

        learning = vd.generate_learning_candidate(self.conn, action["id"], {
            "supported": True, "counterEvidence": "样本量仍有限", "alternativeExplanations": ["销售跟进效率变化"],
            "applicability": "上市期纯电SUV", "nonApplicability": "价格大幅变化期"
        }, org_id="org-a", user_id="ellis", as_of="2026-07-21")
        self.assertEqual(learning["status"], "pending_review")
        approved = vd.review_learning_candidate(self.conn, learning["id"], "approved", "证据边界完整", org_id="org-a", user_id="ellis")
        self.assertEqual(approved["status"], "approved")
        self.assertIs(approved["supported"], True)
        with self.assertRaisesRegex(ValueError, "重复验证"):
            vd.generate_knowhow_candidate(self.conn, {"learningIds": [learning["id"]]}, org_id="org-a", user_id="ellis")
        candidate = vd.generate_knowhow_candidate(self.conn, {"learningIds": [learning["id"]], "ellisWaiver": True, "waiverReason": "隔离验收，不进入正式客户知识库"}, org_id="org-a", user_id="ellis")
        self.assertEqual(candidate["status"], "pending_review")
        knowhow = vd.review_knowhow_candidate(self.conn, candidate["id"], "approved", "仅批准隔离测试边界", org_id="org-a", user_id="ellis")
        self.assertEqual(knowhow["status"], "approved")
        knowledge = vd.list_approved_knowledge(self.conn, org_id="org-a", edition="china", model="AUDI E7X")
        self.assertEqual(len(knowledge["learnings"]), 1)
        self.assertEqual(len(knowledge["knowhows"]), 1)

    def test_org_isolation_and_exports(self):
        snapshot = self.snapshot()
        report = vd.generate_report(self.conn, snapshot["id"], org_id="org-a", user_id="ellis")
        with self.assertRaisesRegex(LookupError, "不存在"):
            vd.get_snapshot(self.conn, snapshot["id"], org_id="org-b")
        markdown = vd.render_report_markdown(report)
        self.assertIn("AUDI E7X", markdown)
        self.assertIn("证据与缺口", markdown)
        pptx = vd.render_report_pptx(report)
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(pptx)))

    def test_nsr_validation_adjudication_persists_links_without_changing_baseline(self):
        saved = vd.adjudicate_nsr_validation(
            self.conn, "mart-1", "target-cockpit", "supported", "原文支持且车型标签一致",
            ["evidence-2", "evidence-1", "evidence-1"], org_id="org-a", user_id="ellis",
        )
        self.assertEqual(saved["evidenceIds"], ["evidence-1", "evidence-2"])
        listed = vd.list_nsr_validation_adjudications(self.conn, "mart-1", org_id="org-a")
        self.assertEqual(listed[0]["decision"], "supported")
        self.assertEqual(listed[0]["targetId"], "target-cockpit")
        self.assertEqual(listed[0]["evidenceIds"], ["evidence-1", "evidence-2"])
        rejected = vd.adjudicate_nsr_validation(
            self.conn, "mart-1", "target-luxury", "mixed", "正反样本同时存在",
            ["evidence-3"], org_id="org-a", user_id="ellis",
        )
        self.assertEqual(rejected["evidenceIds"], [])
        self.assertEqual(rejected["reviewedEvidenceIds"], ["evidence-3"])
        self.assertEqual(vd.list_nsr_validation_adjudications(self.conn, "mart-1", org_id="org-b"), [])
        columns = {row[1] for row in self.conn.execute("pragma table_info(human_adjudications)")}
        self.assertNotIn("baseline_nsr", columns)

    def test_action_edition_dates_and_completion_rate_are_validated(self):
        snapshot = self.snapshot()
        report = vd.generate_report(self.conn, snapshot["id"], org_id="org-a", user_id="ellis")
        report = vd.publish_report(self.conn, report["id"], org_id="org-a", user_id="ellis", approval_note="边界测试批准")
        body = {
            "reportId": report["id"], "decisionId": report["content"]["topDecisions"][0]["signalId"],
            "hypothesis": "边界测试", "owner": "负责人", "target": "对象", "platform": "平台",
            "region": "上海", "audience": "人群", "startAt": "2026-07-22", "endAt": "2026-07-21",
            "baseline": {"rate": .1}, "targetValue": {"rate": .2}, "leadingIndicator": "领先指标",
            "resultIndicator": "结果指标", "stopCondition": "停止条件",
        }
        with self.assertRaisesRegex(ValueError, "版本"):
            vd.create_action(self.conn, body, org_id="org-a", user_id="ellis", edition="global")
        with self.assertRaisesRegex(ValueError, "时间"):
            vd.create_action(self.conn, body, **self.scope)
        body["startAt"] = "2026-07-21"
        action = vd.create_action(self.conn, body, **self.scope)
        vd.update_action_status(self.conn, action["id"], "running", org_id="org-a", user_id="ellis")
        with self.assertRaisesRegex(ValueError, "完成度"):
            vd.record_result(self.conn, action["id"], {
                "metrics": {}, "actualExecution": "边界测试", "completionRate": 1.2,
                "actualTimeWindow": "2026-07-21",
            }, org_id="org-a", user_id="ellis")


if __name__ == "__main__":
    unittest.main()
