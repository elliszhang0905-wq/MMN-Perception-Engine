import tempfile
import unittest
from pathlib import Path

from cockpit_decision_loop import derive_execution_recommendations
import server


class CockpitDecisionLoopTest(unittest.TestCase):
    def setUp(self):
        self.original_db_path = server.DB_PATH
        self.tempdir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(self.tempdir.name) / "cockpit-loop.db"
        server.init_db()

    def tearDown(self):
        server.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_only_dual_model_verified_opportunities_become_execution_recommendations(self):
        recommendations = derive_execution_recommendations(
            [
                {
                    "label": "舒适性",
                    "category": "seize",
                    "categoryLabel": "抢占空位",
                    "evidenceStatus": "aligned",
                    "commonEvidenceIds": ["fact-comfort"],
                    "leadCompetitorModel": "竞品A",
                    "factStrength": 0.86,
                },
                {
                    "label": "价格",
                    "category": "manual_required",
                    "evidenceStatus": "manual_required",
                    "commonEvidenceIds": [],
                },
            ],
            [
                {"label": "舒适性", "platform": "抖音", "volume": 80, "interaction": 160},
                {"label": "舒适性", "platform": "小红书", "volume": 50, "interaction": 480},
            ],
        )

        self.assertEqual(len(recommendations), 1)
        item = recommendations[0]
        self.assertEqual(item["label"], "舒适性")
        self.assertEqual(item["competitorModel"], "竞品A")
        self.assertEqual(item["platform"], "小红书")
        self.assertEqual(item["action"], "对比占位")
        self.assertIn("舒适", item["contentScenario"])
        self.assertEqual(item["evidenceIds"], ["fact-comfort"])
        self.assertEqual(item["recommendedOptionId"], "comparison_occupy")
        self.assertEqual(
            [option["id"] for option in item["options"]],
            ["comparison_occupy", "scenario_compete", "search_answer"],
        )

    def test_execution_requires_a_valid_human_selected_strategy_option(self):
        run_id = "opportunity-run-options"
        server.save_agent_run_record(
            {
                "id": run_id,
                "org_id": "local",
                "user_id": "tester",
                "edition": "china",
                "task_type": "opportunity_map",
                "brand": "本品",
                "model": "本品车型",
                "competitors": ["竞品A"],
                "platforms": ["小红书"],
                "status": "completed",
                "final_output": {
                    "opportunities": [{
                        "label": "舒适性",
                        "category": "seize",
                        "evidenceStatus": "aligned",
                        "commonEvidenceIds": ["fact-comfort"],
                        "leadCompetitorModel": "竞品A",
                    }],
                    "executionRecommendations": [{
                        "label": "舒适性",
                        "competitorModel": "竞品A",
                        "platform": "小红书",
                        "action": "对比占位",
                        "contentScenario": "长途乘坐舒适体验",
                        "evidenceIds": ["fact-comfort"],
                        "recommendedOptionId": "comparison_occupy",
                        "options": [
                            {"id": "comparison_occupy", "title": "对比占位", "contentScenario": "长途乘坐舒适体验"},
                            {"id": "scenario_compete", "title": "场景对比切入", "contentScenario": "多人出行舒适对比"},
                        ],
                    }],
                },
                "qa_summary": {},
                "created_at": "2026-07-11T03:00:00Z",
                "updated_at": "2026-07-11T03:00:00Z",
            },
            [],
            [],
            [],
        )

        with self.assertRaisesRegex(ValueError, "请选择策略选项"):
            server.create_cockpit_execution_cycle({"runId": run_id, "label": "舒适性"}, org_id="local")
        with self.assertRaisesRegex(ValueError, "不存在"):
            server.create_cockpit_execution_cycle(
                {"runId": run_id, "label": "舒适性", "optionId": "not-an-option"},
                org_id="local",
            )

        cycle = server.create_cockpit_execution_cycle(
            {"runId": run_id, "label": "舒适性", "optionId": "scenario_compete"},
            org_id="local",
        )
        self.assertEqual(cycle["plan"]["selectedOption"]["id"], "scenario_compete")
        self.assertEqual(cycle["plan"]["selectedOption"]["title"], "场景对比切入")

    def test_execution_monitoring_is_persisted_as_feedback_for_the_next_map_run(self):
        run_id = "opportunity-run-1"
        server.save_agent_run_record(
            {
                "id": run_id,
                "org_id": "local",
                "user_id": "tester",
                "edition": "china",
                "task_type": "opportunity_map",
                "brand": "本品",
                "model": "本品车型",
                "competitors": ["竞品A"],
                "platforms": ["小红书"],
                "status": "completed",
                "final_output": {
                    "opportunities": [
                        {
                            "label": "舒适性",
                            "category": "seize",
                            "evidenceStatus": "aligned",
                            "commonEvidenceIds": ["fact-comfort"],
                            "leadCompetitorModel": "竞品A",
                            "factStrength": 0.86,
                        }
                    ],
                    "executionRecommendations": [
                        {
                            "label": "舒适性",
                            "competitorModel": "竞品A",
                            "platform": "小红书",
                            "action": "对比占位",
                            "contentScenario": "长途乘坐舒适体验",
                            "evidenceIds": ["fact-comfort"],
                            "recommendedOptionId": "comparison_occupy",
                            "options": [
                                {"id": "comparison_occupy", "title": "对比占位", "contentScenario": "长途乘坐舒适体验"},
                                {"id": "scenario_compete", "title": "场景对比切入", "contentScenario": "多人出行舒适对比"},
                            ],
                        }
                    ],
                },
                "qa_summary": {},
                "created_at": "2026-07-11T03:00:00Z",
                "updated_at": "2026-07-11T03:00:00Z",
            },
            [],
            [],
            [],
        )

        cycle = server.create_cockpit_execution_cycle(
            {"runId": run_id, "label": "舒适性", "optionId": "scenario_compete"},
            org_id="local",
            user_id="tester",
        )
        self.assertEqual(cycle["status"], "planned")
        self.assertEqual(cycle["plan"]["competitorModel"], "竞品A")
        self.assertEqual(cycle["plan"]["selectedOption"]["id"], "scenario_compete")

        monitored = server.record_cockpit_execution_monitoring(
            {
                "cycleId": cycle["id"],
                "volume": 120,
                "interaction": 360,
                "nsr": 0.42,
                "observation": "小红书收藏和评论均高于预期",
            },
            org_id="local",
        )
        self.assertEqual(monitored["status"], "feedback_recorded")
        self.assertEqual(monitored["feedbackSignal"]["attribute"], "舒适性")
        self.assertEqual(monitored["feedbackSignal"]["platform"], "小红书")

        payload = server.cockpit_execution_cycles_payload("china", "本品车型", org_id="local")
        self.assertEqual(len(payload["cycles"]), 1)
        self.assertEqual(payload["cycles"][0]["monitoring"]["interaction"], 360)
        self.assertEqual(payload["feedbackSignals"][0]["nsr"], 0.42)


if __name__ == "__main__":
    unittest.main()
