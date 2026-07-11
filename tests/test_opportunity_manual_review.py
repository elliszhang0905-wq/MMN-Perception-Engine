import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class OpportunityManualReviewTest(unittest.TestCase):
    def setUp(self):
        self.original_db_path = server.DB_PATH
        self.tempdir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(self.tempdir.name) / "manual-review.db"
        server.init_db()
        payload = {
            "documentId": "doc-review",
            "filename": "产品白皮书.pdf",
            "brand": "奥迪",
            "model": "奥迪E7X",
            "version": "V260410",
            "facts": [
                {
                    "id": "fact-1",
                    "claim": "科技配置与舒适座椅全面升级",
                    "labels": ["配置", "舒适性"],
                    "evidence": {"pageNo": 12, "sourceRef": "产品白皮书.pdf", "excerpt": "科技配置与舒适座椅全面升级"},
                }
            ],
            "manualReviewItems": [
                {"type": "fact_alignment", "claim": "科技配置与舒适座椅全面升级", "labels": ["配置", "舒适性"]},
                {"type": "fact_alignment_summary", "status": "unmatched", "count": 3, "reason": "部分文本未能唯一归入统一标签"},
            ],
        }
        with server.db() as conn:
            conn.execute(
                """insert into product_fact_documents
                (id, org_id, user_id, edition, brand, model, version, filename, sha256, storage_path, payload_json, created_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("doc-review", "local", "tester", "china", "奥迪", "奥迪E7X", "V260410", payload["filename"], "sha", "", json.dumps(payload, ensure_ascii=False), "2026-07-11T02:38:31Z"),
            )

    def tearDown(self):
        server.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_review_queue_exposes_evidence_candidates_and_progress(self):
        queue = server.opportunity_manual_review_payload("doc-review")

        self.assertEqual(queue["counts"], {"total": 2, "pending": 2, "pendingRecheck": 0, "needsEvidence": 0, "processed": 0, "blocking": 2})
        first = queue["items"][0]
        self.assertEqual(first["candidateLabels"], ["配置", "舒适性"])
        self.assertEqual(first["evidence"]["pageNo"], 12)
        self.assertEqual(first["status"], "pending")
        self.assertIn("多个统一标签", first["reasons"][0])

    def test_decision_is_persisted_with_selected_label_and_note(self):
        queue = server.opportunity_manual_review_payload("doc-review")
        item_id = queue["items"][0]["id"]

        saved = server.save_opportunity_manual_review({
            "documentId": "doc-review",
            "itemId": item_id,
            "action": "corrected",
            "selectedLabel": "舒适性",
            "note": "该页核心描述为座椅舒适体验",
        }, user_id="ellis")

        self.assertEqual(saved["decision"]["action"], "corrected")
        self.assertEqual(saved["decision"]["selectedLabel"], "舒适性")
        refreshed = server.opportunity_manual_review_payload("doc-review")
        self.assertEqual(refreshed["counts"], {"total": 2, "pending": 1, "pendingRecheck": 1, "needsEvidence": 0, "processed": 0, "blocking": 2})
        decided = next(item for item in refreshed["items"] if item["id"] == item_id)
        self.assertEqual(decided["status"], "corrected_pending_recheck")
        self.assertEqual(decided["decision"]["note"], "该页核心描述为座椅舒适体验")

        applied = server.apply_opportunity_manual_decisions({
            "documentId": "doc-review",
            "facts": [{"id": "fact-1", "claim": "科技配置与舒适座椅全面升级", "labels": ["配置", "舒适性"], "alignmentStatus": "ambiguous"}],
        })
        self.assertEqual(applied["facts"][0]["label"], "舒适性")
        self.assertEqual(applied["facts"][0]["alignmentStatus"], "human_corrected_pending_recheck")

        verified_count = server.finalize_opportunity_manual_rechecks(
            "doc-review",
            {"items": [{"label": "舒适性", "evidenceStatus": "aligned", "commonEvidenceIds": ["fact-1"]}]},
            models_verified=True,
        )
        self.assertEqual(verified_count, 1)
        verified_queue = server.opportunity_manual_review_payload("doc-review")
        self.assertEqual(verified_queue["counts"], {"total": 2, "pending": 1, "pendingRecheck": 0, "needsEvidence": 0, "processed": 1, "blocking": 1})
        verified_document = server.apply_opportunity_manual_decisions(applied)
        self.assertEqual(verified_document["facts"][0]["alignmentStatus"], "human_verified")
        self.assertEqual(len(verified_document["manualReviewItems"]), 1)

    def test_recheck_requires_both_models_to_cite_the_corrected_fact(self):
        queue = server.opportunity_manual_review_payload("doc-review")
        item_id = queue["items"][0]["id"]
        server.save_opportunity_manual_review({
            "documentId": "doc-review",
            "itemId": item_id,
            "action": "corrected",
            "selectedLabel": "舒适性",
            "note": "该页核心描述为座椅舒适体验",
        }, user_id="ellis")

        label_only_count = server.finalize_opportunity_manual_rechecks(
            "doc-review",
            {"items": [{"label": "舒适性", "evidenceStatus": "aligned", "commonEvidenceIds": []}]},
            models_verified=True,
        )
        self.assertEqual(label_only_count, 0)
        self.assertEqual(
            server.opportunity_manual_review_payload("doc-review")["counts"]["pendingRecheck"],
            1,
        )

        item_verified_count = server.finalize_opportunity_manual_rechecks(
            "doc-review",
            {"items": [{"label": "舒适性", "evidenceStatus": "aligned", "commonEvidenceIds": ["fact-1"]}]},
            models_verified=True,
        )
        self.assertEqual(item_verified_count, 1)
        self.assertEqual(
            server.opportunity_manual_review_payload("doc-review")["counts"]["processed"],
            1,
        )

    def test_pipeline_recheck_verifies_correction_and_recomputes_map_position(self):
        item_id = server.opportunity_manual_review_payload("doc-review")["items"][0]["id"]
        server.save_opportunity_manual_review({
            "documentId": "doc-review",
            "itemId": item_id,
            "action": "corrected",
            "selectedLabel": "舒适性",
            "note": "该页核心描述为座椅舒适体验",
        }, user_id="ellis")
        model_item = {
            "label": "舒适性",
            "factStrength": 0.85,
            "direction": "seize",
            "reason": "座椅舒适事实成立",
            "evidenceIds": ["fact-1", "competitor-comfort"],
            "confidence": 0.9,
        }
        source_result = {
            "url": "https://example.com/competitor",
            "finalUrl": "https://example.com/competitor",
            "fetchedAt": "2026-07-11T03:00:00Z",
            "sha256": "source-sha",
            "status": "verified",
            "brand": "竞品",
            "model": "竞品A",
            "version": "",
        }
        body = {
            "documentId": "doc-review",
            "edition": "china",
            "competitorSources": [{"model": "竞品A", "url": source_result["url"]}],
            "marketSignals": [
                {"model": "奥迪E7X", "attribute": "舒适性", "nsr": 0.4, "volume": 100, "interaction": 500, "purchaseImpact": 5},
                {"model": "竞品A", "attribute": "舒适性", "nsr": 0.7, "volume": 200, "interaction": 600, "purchaseImpact": 4},
            ],
        }

        competitor_fact = {
            "id": "competitor-comfort", "label": "舒适性", "alignmentStatus": "aligned",
            "claim": "前后排座椅通风加热", "confidence": 0.85,
            "sourceModel": "竞品A", "sourceUrl": source_result["finalUrl"],
        }
        with patch.object(server, "collect_opportunity_official_sources", return_value=([competitor_fact], [source_result])), \
                patch.object(server, "_opportunity_model_analysis", side_effect=[([model_item], "model", ""), ([dict(model_item)], "model", "")]), \
                patch.object(server, "save_agent_run_record"):
            result = server.run_opportunity_map_pipeline(body, run_id="run-recheck")

        queue = server.opportunity_manual_review_payload("doc-review")
        verified = next(item for item in queue["items"] if item["id"] == item_id)
        opportunity = next(item for item in result["opportunities"] if item["label"] == "舒适性")
        self.assertEqual(result["status"], "partial_completed")
        self.assertEqual(verified["status"], "verified")
        self.assertEqual(result["document"]["facts"][0]["alignmentStatus"], "human_verified")
        self.assertEqual(opportunity["category"], "seize")
        self.assertAlmostEqual(opportunity["mapX"], 0.3)
        self.assertEqual(opportunity["mapY"], 5.0)
        self.assertEqual(result["competitorProducts"][0]["coreProductStrengths"][0]["label"], "舒适性")
        self.assertEqual(result["competitorProducts"][0]["coreProductStrengths"][0]["claim"], "前后排座椅通风加热")

    def test_pipeline_does_not_invent_a_quadrant_without_competitor_attribute_nsr(self):
        model_item = {
            "label": "舒适性", "factStrength": 0.85, "direction": "seize",
            "evidenceIds": ["fact-1"], "confidence": 0.9,
        }
        source_result = {
            "url": "https://example.com/competitor", "finalUrl": "https://example.com/competitor",
            "fetchedAt": "2026-07-11T03:00:00Z", "sha256": "source-sha", "status": "verified",
            "brand": "竞品", "model": "竞品A", "version": "",
        }
        body = {
            "documentId": "doc-review",
            "competitorSources": [{"model": "竞品A", "url": source_result["url"]}],
            "marketSignals": [
                {"model": "奥迪E7X", "attribute": "舒适性", "nsr": 0.4, "volume": 100, "interaction": 500, "purchaseImpact": 5},
            ],
        }

        with patch.object(server, "collect_opportunity_official_sources", return_value=([], [source_result])), \
                patch.object(server, "_opportunity_model_analysis", side_effect=[([model_item], "model", ""), ([dict(model_item)], "model", "")]), \
                patch.object(server, "save_agent_run_record"):
            result = server.run_opportunity_map_pipeline(body, run_id="run-missing-competitor-nsr")

        opportunity = next(item for item in result["opportunities"] if item["label"] == "舒适性")
        self.assertEqual(opportunity["category"], "manual_required")
        self.assertIn("缺少竞品属性NSR", opportunity["manualReasons"])

    def test_model_prompt_prioritizes_pending_manual_corrections_before_truncation(self):
        regular_facts = [
            {"id": f"regular-{index}", "claim": "常规产品事实" + ("很长" * 300), "label": "配置", "alignmentStatus": "aligned"}
            for index in range(150)
        ]
        pending = {
            "id": "pending-fact",
            "claim": "必须进入双模型复核的人工修正",
            "label": "舒适性",
            "alignmentStatus": "human_corrected_pending_recheck",
        }
        facts = regular_facts + [pending]
        packet = {"own": {"documentId": "doc-review", "facts": facts}, "marketSignals": [], "competitorFacts": []}

        with patch.object(server, "qwen_config", return_value={"configured": True}), \
                patch.object(server, "call_qwen", return_value="[]") as call:
            _, mode, error = server._opportunity_model_analysis("qwen", packet, facts)

        prompt_text = call.call_args.args[0][1]["content"]
        self.assertEqual(mode, "model")
        self.assertEqual(error, "")
        self.assertIn("pending-fact", prompt_text)
        self.assertLess(prompt_text.index("pending-fact"), 10000)

    def test_bulk_needs_evidence_decision_updates_selected_items(self):
        item_ids = [item["id"] for item in server.opportunity_manual_review_payload("doc-review")["items"]]

        saved = server.save_opportunity_manual_review({
            "documentId": "doc-review",
            "itemIds": item_ids,
            "action": "needs_evidence",
            "note": "请产品团队补充版本适用范围",
        }, user_id="ellis")

        self.assertEqual(saved["savedCount"], 2)
        self.assertEqual(server.opportunity_manual_review_payload("doc-review")["counts"], {"total": 2, "pending": 0, "pendingRecheck": 0, "needsEvidence": 2, "processed": 0, "blocking": 2})

    def test_reapplying_after_rejection_preserves_later_review_item_identity(self):
        payload = server._opportunity_document_payload("doc-review")
        payload["facts"] = [
            {"id": "fact-1", "claim": "科技配置与舒适座椅全面升级", "labels": ["配置", "舒适性"], "alignmentStatus": "ambiguous"},
            {"id": "fact-2", "claim": "后排座椅提供加热通风", "labels": ["配置", "舒适性"], "alignmentStatus": "ambiguous"},
        ]
        payload["manualReviewItems"] = [
            {"type": "fact_alignment", "claim": "科技配置与舒适座椅全面升级", "labels": ["配置", "舒适性"]},
            {"type": "fact_alignment", "claim": "后排座椅提供加热通风", "labels": ["配置", "舒适性"]},
        ]
        with server.db() as conn:
            conn.execute(
                "update product_fact_documents set payload_json=? where id='doc-review'",
                (json.dumps(payload, ensure_ascii=False),),
            )
        queue = server.opportunity_manual_review_payload("doc-review")
        first_id, second_id = [item["id"] for item in queue["items"]]
        server.save_opportunity_manual_review({
            "documentId": "doc-review", "itemId": first_id, "action": "rejected", "note": "非产品事实",
        })
        server.save_opportunity_manual_review({
            "documentId": "doc-review", "itemId": second_id, "action": "corrected", "selectedLabel": "舒适性", "note": "核心是座椅体验",
        })

        first_pass = server.apply_opportunity_manual_decisions(payload)
        self.assertEqual([fact["id"] for fact in first_pass["facts"]], ["fact-2"])
        server.finalize_opportunity_manual_rechecks(
            "doc-review",
            {"items": [{"label": "舒适性", "evidenceStatus": "aligned", "commonEvidenceIds": ["fact-2"]}]},
            models_verified=True,
        )
        second_pass = server.apply_opportunity_manual_decisions(first_pass)

        self.assertEqual(second_pass["manualReviewItems"], [])
        self.assertEqual(second_pass["facts"][0]["alignmentStatus"], "human_verified")

    def test_invalid_label_and_risky_bulk_correction_are_rejected(self):
        item_ids = [item["id"] for item in server.opportunity_manual_review_payload("doc-review")["items"]]
        with self.assertRaisesRegex(ValueError, "统一标签"):
            server.save_opportunity_manual_review({
                "documentId": "doc-review",
                "itemId": item_ids[0],
                "action": "corrected",
                "selectedLabel": "随便写的标签",
                "note": "测试",
            })
        with self.assertRaisesRegex(ValueError, "批量"):
            server.save_opportunity_manual_review({
                "documentId": "doc-review",
                "itemIds": item_ids,
                "action": "corrected",
                "selectedLabel": "舒适性",
                "note": "测试",
            })
        with self.assertRaisesRegex(ValueError, "不对应单一产品事实"):
            server.save_opportunity_manual_review({
                "documentId": "doc-review",
                "itemId": item_ids[1],
                "action": "corrected",
                "selectedLabel": "舒适性",
                "note": "不能把汇总项整体归到一个标签",
            })


if __name__ == "__main__":
    unittest.main()
