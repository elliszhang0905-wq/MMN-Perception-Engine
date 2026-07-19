import unittest
from unittest import mock

import mmn_model_governance as governance


class MmnModelGovernanceTest(unittest.TestCase):
    def test_contract_covers_all_eight_cockpit_surfaces(self):
        self.assertEqual(
            set(governance.COCKPIT_SURFACE_POLICIES),
            {"brief", "implication", "warning", "market", "policy", "competitive", "platform", "attribute"},
        )

    def test_global_task_router_has_explicit_auditor_rules(self):
        required = {
            "strategy_reasoning", "content_delivery", "fact_explanation",
            "vehicle_configuration_fact", "data_summary", "fast_strategy", "complex_strategy",
        }
        self.assertEqual(set(governance.TASK_ROUTER_POLICIES), required)
        for policy in governance.TASK_ROUTER_POLICIES.values():
            self.assertIn("auditorMode", policy)

    def test_models_are_independent_and_cannot_call_peers(self):
        protocol = governance.INDEPENDENCE_PROTOCOL
        self.assertTrue(protocol["sameEvidencePacket"])
        self.assertTrue(protocol["blindIndependentFirstPass"])
        self.assertFalse(protocol["modelsMayCallEachOther"])
        self.assertFalse(protocol["modelsMaySeePeerOutputBeforeFirstPass"])

    def test_policy_always_requires_three_independent_roles(self):
        route = governance.resolve_surface_route("policy", {"evidenceCount": 3})
        self.assertEqual(route["mode"], "triple_parallel")
        self.assertTrue(route["auditorRequired"])
        self.assertEqual(set(route["roles"]), {"reasoning_lead", "business_editor", "evidence_auditor"})
        self.assertEqual(route["publicationGate"], "three_independent_common_evidence")

    def test_sales_warning_keeps_deterministic_fact_ownership(self):
        route = governance.resolve_surface_route("warning", {"evidenceCount": 8})
        self.assertEqual(route["factOwner"], "deterministic_sales_rules")
        self.assertFalse(route["auditorRequired"])
        escalated = governance.resolve_surface_route("warning", {"evidenceCount": 8, "thresholdDispute": True})
        self.assertTrue(escalated["auditorRequired"])

    def test_executive_summary_uses_risk_based_auditor_escalation(self):
        normal = governance.resolve_surface_route("brief", {"evidenceCount": 4, "confidence": 0.9})
        self.assertFalse(normal["auditorRequired"])
        conflict = governance.resolve_surface_route("brief", {"evidenceCount": 4, "conflict": True, "confidence": 0.6})
        self.assertTrue(conflict["auditorRequired"])
        self.assertEqual(conflict["state"], "reviewing")

    def test_missing_evidence_never_becomes_a_publishable_conclusion(self):
        route = governance.resolve_surface_route("competitive", {"evidenceCount": 0})
        self.assertEqual(route["state"], "insufficient_evidence")

    def test_state_machine_rejects_invalid_shortcut(self):
        self.assertEqual(governance.transition_state("aligned", "published"), "published")
        with self.assertRaises(ValueError):
            governance.transition_state("draft", "published")

    def test_runtime_budget_overrides_are_bounded(self):
        with mock.patch.dict("os.environ", {"MMN_MODEL_DECISION_BUDGET_UNITS": "999"}):
            self.assertEqual(governance.runtime_guardrails()["perDecisionBudgetUnits"], 20)

    def test_eval_contract_has_quality_latency_and_cost_gates(self):
        metrics = governance.EVAL_CONTRACT["metrics"]
        for key in ("factualAccuracy", "evidenceCoverage", "unsupportedClaimRate", "strategyExecutability",
                    "conflictRecall", "p95FirstResultSeconds", "p95FinalReviewSeconds", "costUnitsPerAcceptedDecision"):
            self.assertIn(key, metrics)

    def test_experiment_assignment_is_stable(self):
        first = governance.assign_experiment_arm("org-1:model-a")
        self.assertEqual(first, governance.assign_experiment_arm("org-1:model-a"))
        self.assertIn(first, {"control", "treatment"})

    def test_public_contract_does_not_expose_provider_names(self):
        raw = str(governance.public_model_governance_contract()).lower()
        for provider in ("qwen", "deepseek", "kimi"):
            self.assertNotIn(provider, raw)

    def test_cockpit_snapshot_reports_actual_review_states(self):
        snapshot = governance.cockpit_governance_snapshot({
            "executiveBrief": {"status": "verified", "facts": {"retail": 1}},
            "salesWarnings": {"saicModels": [{"model": "A"}], "dualModelReview": {"status": "pending_review"}},
            "marketDimensions": [{"id": "suv"}],
            "policyIntelligence": {"models": [{"vehicleImpact": {"policyEffects": [{"policyId": "p1"}]}}]},
            "productEvaluation": {"models": [{"model": "A"}], "platforms": [{"name": "P"}], "attributes": [{"name": "X"}]},
        })
        self.assertEqual(snapshot["surfaces"]["brief"]["state"], "aligned")
        self.assertEqual(snapshot["surfaces"]["warning"]["state"], "reviewing")
        self.assertEqual(snapshot["surfaces"]["policy"]["mode"], "triple_parallel")


if __name__ == "__main__":
    unittest.main()
