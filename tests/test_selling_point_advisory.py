import json
import sqlite3
import unittest

import selling_point_advisory as advisory


def evidence_items(*, complete=False, conflict=False):
    statuses = ["verified", "conflict" if conflict else "verified", "verified", "verified" if complete else "partial", "verified" if complete else "missing"]
    categories = ["market_fact", "user_perception", "competitor_performance", "product_capability", "communication_content"]
    return [
        {
            "evidenceId": f"evidence-{index + 1}",
            "category": category,
            "fact": f"事实 {index + 1}",
            "status": statuses[index],
            "impact": f"判断影响 {index + 1}",
            "sourceRefs": [f"source-{index + 1}"],
            "timeRange": "2026-06-01/2026-06-30",
            "sampleScope": "当前车型与当前标签",
            "limitations": "仅适用于当前证据窗口",
        }
        for index, category in enumerate(categories)
    ]


def context(*, complete=False, conflict=False, label="安全"):
    return {
        "edition": "china",
        "brand": "奥迪",
        "model": "奥迪E7X",
        "competitor": "问界M7",
        "label": label,
        "tCycle": {"phase": "sales_conversion", "display": "T+49"},
        "evidencePacket": {
            "items": evidence_items(complete=complete, conflict=conflict),
            "conflicts": ["evidence-2"] if conflict else [],
            "gaps": [] if complete else ["evidence-5"],
            "windowCoverage": 0.11,
            "updatedAt": "2026-07-21T09:00:00Z",
        },
    }


def completed_review(verdict="optimize_expression", cited=None, summary="产品能力具备基础，但认知尚未稳定"):
    return {
        "state": "completed",
        "verdict": verdict,
        "summary": summary,
        "rationale": "依据锁定证据形成独立判断",
        "recommendedAction": "先复核用户语言，再决定是否放大",
        "uncertainty": "当前结论只适用于证据窗口",
        "citedEvidenceIds": ["evidence-1", "evidence-2"] if cited is None else cited,
    }


class SellingPointAdvisoryTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        advisory.init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_locked_packet_has_all_five_fact_categories_and_boundaries(self):
        packet = advisory.build_locked_evidence_packet(context())
        self.assertEqual(len(packet["items"]), 5)
        self.assertEqual({item["category"] for item in packet["items"]}, set(advisory.EVIDENCE_CATEGORIES))
        for item in packet["items"]:
            self.assertEqual(
                set(item),
                {"evidenceId", "category", "fact", "status", "impact", "sourceRefs", "timeRange", "sampleScope", "limitations"},
            )
        self.assertEqual(packet["fingerprint"], advisory.evidence_packet_fingerprint({k: v for k, v in packet.items() if k != "fingerprint"}))

    def test_three_blind_reviews_receive_identical_packet_without_peer_answers(self):
        calls = []

        def runner(role, messages):
            calls.append((role, json.loads(messages[-1]["content"]), json.dumps(messages, ensure_ascii=False)))
            return completed_review()

        result = advisory.run_advisory(self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=runner)
        self.assertEqual(result["status"], "aligned")
        self.assertEqual(len(calls), 3)
        self.assertEqual(len({json.dumps(call[1], sort_keys=True, ensure_ascii=False) for call in calls}), 1)
        self.assertTrue(all("peer" not in call[2].lower() and "其他建议" not in call[2] for call in calls))
        self.assertEqual(len({review["evidenceFingerprint"] for review in result["reviews"]}), 1)

    def test_invalid_or_missing_citations_do_not_count_as_completed(self):
        def runner(role, messages):
            return completed_review(cited=[] if role == advisory.REVIEW_ROLES[0] else ["invented-evidence"])

        result = advisory.run_advisory(self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=runner)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["completedCount"], 0)
        self.assertFalse(result["canEnterMarketingAction"])

    def test_insufficient_evidence_cannot_publish_even_when_three_reviews_agree(self):
        result = advisory.run_advisory(
            self.conn, context(complete=False), org_id="org-a", user_id="ellis", role_runner=lambda *_: completed_review()
        )
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["readiness"]["level"], "low")
        self.assertFalse(result["canEnterMarketingAction"])

    def test_one_failure_is_degraded_and_never_claims_three_way_alignment(self):
        def runner(role, messages):
            if role == advisory.REVIEW_ROLES[-1]:
                raise TimeoutError("通道超时")
            return completed_review()

        result = advisory.run_advisory(self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=runner)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["completedCount"], 2)
        self.assertNotEqual(result["synthesis"]["alignment"], "aligned")

    def test_retry_only_calls_failed_channel_and_keeps_completed_reviews(self):
        first_calls = []

        def first_runner(role, messages):
            first_calls.append(role)
            if role == advisory.REVIEW_ROLES[-1]:
                raise TimeoutError("通道超时")
            return completed_review()

        first = advisory.run_advisory(self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=first_runner)
        retry_calls = []
        second = advisory.run_advisory(
            self.conn,
            context(complete=True),
            org_id="org-a",
            user_id="ellis",
            force=True,
            role_runner=lambda role, messages: retry_calls.append(role) or completed_review(),
        )
        self.assertEqual(len(first_calls), 3)
        self.assertEqual(retry_calls, [advisory.REVIEW_ROLES[-1]])
        self.assertEqual(first["runId"], second["runId"])
        self.assertEqual(second["status"], "aligned")

    def test_shared_evidence_with_explicit_disagreement_is_partially_aligned(self):
        reviews = {
            advisory.REVIEW_ROLES[0]: completed_review("optimize_expression", ["evidence-1"]),
            advisory.REVIEW_ROLES[1]: completed_review("optimize_expression", ["evidence-1"]),
            advisory.REVIEW_ROLES[2]: completed_review("hold", ["evidence-1"]),
        }
        result = advisory.run_advisory(
            self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=lambda role, _: reviews[role]
        )
        self.assertEqual(result["status"], "partially_aligned")
        self.assertEqual(result["synthesis"]["alignment"], "partial")
        self.assertTrue(result["synthesis"]["disagreements"])

    def test_all_channels_failed_preserves_evidence_without_fake_reviews(self):
        def runner(role, messages):
            raise RuntimeError("服务暂不可用")

        result = advisory.run_advisory(self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=runner)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["completedCount"], 0)
        self.assertEqual(result["reviews"], [])
        self.assertEqual(len(result["evidencePacket"]["items"]), 5)
        self.assertEqual(result["synthesis"]["nextAction"], "重试失败通道")

    def test_aggregation_checks_common_evidence_and_disagreement_not_just_majority(self):
        reviews = {
            advisory.REVIEW_ROLES[0]: completed_review("amplify", ["evidence-1"]),
            advisory.REVIEW_ROLES[1]: completed_review("amplify", ["evidence-2"]),
            advisory.REVIEW_ROLES[2]: completed_review("repair", ["evidence-3"]),
        }
        result = advisory.run_advisory(
            self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=lambda role, _: reviews[role]
        )
        self.assertEqual(result["status"], "manual_required")
        self.assertEqual(result["synthesis"]["citedEvidenceIds"], [])
        self.assertFalse(result["canEnterMarketingAction"])

    def test_cache_reuses_same_fingerprint_and_changed_packet_marks_old_run_stale(self):
        calls = []

        def runner(role, messages):
            calls.append(role)
            return completed_review()

        first = advisory.run_advisory(self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=runner)
        second = advisory.run_advisory(self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=runner)
        changed = context(complete=True)
        changed["evidencePacket"]["items"][0]["fact"] = "更新后的事实"
        third = advisory.run_advisory(self.conn, changed, org_id="org-a", user_id="ellis", role_runner=runner)
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(len(calls), 6)
        stale = advisory.get_run(self.conn, first["runId"], org_id="org-a")
        self.assertEqual(stale["status"], "stale")
        self.assertNotEqual(first["evidenceFingerprint"], third["evidenceFingerprint"])

    def test_latest_restores_matching_fingerprint_and_rejects_mismatch(self):
        request = context(complete=True)
        result = advisory.run_advisory(
            self.conn, request, org_id="org-a", user_id="ellis", role_runner=lambda *_: completed_review()
        )
        matching = {**request, "evidenceFingerprint": result["evidenceFingerprint"]}
        stale = {**request, "evidenceFingerprint": "different-fingerprint"}
        self.assertEqual(advisory.latest_run(self.conn, matching, "org-a")["status"], "aligned")
        self.assertEqual(advisory.latest_run(self.conn, stale, "org-a")["status"], "stale")

    def test_latest_and_manual_review_are_tenant_scoped_and_audited(self):
        result = advisory.run_advisory(
            self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=lambda *_: completed_review()
        )
        self.assertIsNone(advisory.get_run(self.conn, result["runId"], org_id="org-b"))
        reviewed = advisory.record_manual_review(
            self.conn,
            result["runId"],
            org_id="org-a",
            user_id="ellis",
            reason="确认先复核平台差异",
            decision={"verdict": "manual_review", "nextAction": "查看分平台差异"},
        )
        self.assertEqual(reviewed["manualReview"]["operator"], "ellis")
        self.assertEqual(reviewed["manualReview"]["reason"], "确认先复核平台差异")
        self.assertEqual(reviewed["manualReview"]["originalStatus"], "aligned")
        self.assertNotIn("learning", json.dumps(reviewed, ensure_ascii=False).lower())

    def test_public_payload_never_exposes_provider_names(self):
        result = advisory.run_advisory(
            self.conn, context(complete=True), org_id="org-a", user_id="ellis", role_runner=lambda *_: completed_review()
        )
        public = json.dumps(result, ensure_ascii=False).lower()
        for provider in ("qwen", "deepseek", "kimi", "openai"):
            self.assertNotIn(provider, public)


if __name__ == "__main__":
    unittest.main()
