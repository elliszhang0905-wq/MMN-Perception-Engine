import unittest

from creator_distillation.content_validation import (
    build_creator_content_validation, cross_validate_content_models,
)


class CreatorContentValidationTest(unittest.TestCase):
    def test_requires_common_evidence_same_verdict_and_all_domains(self):
        outputs={
            "qwen":{"claims":[
                {"claimKey":"account_positioning","verdict":"expert_education","confidence":.8,"evidenceIds":["e1"]},
                {"claimKey":"topic_focus","verdict":"technical_education","confidence":.7,"evidenceIds":["e1","e2"]},
                {"claimKey":"visual_style","verdict":"talking_head","confidence":.75,"evidenceIds":["v1"]},
            ]},
            "deepseek":{"claims":[
                {"claimKey":"account_positioning","verdict":"expert_education","confidence":.77,"evidenceIds":["e1"]},
                {"claimKey":"topic_focus","verdict":"technical_education","confidence":.72,"evidenceIds":["e2"]},
                {"claimKey":"visual_style","verdict":"talking_head","confidence":.69,"evidenceIds":["v1"]},
            ]},
        }
        result=cross_validate_content_models(outputs,{"e1","e2","v1"},{"v1"},
                                             ["account_positioning","content_dna","visual_conclusion"])
        self.assertEqual(result["status"],"aligned")
        self.assertEqual(result["commonEvidenceIds"],["e1","e2","v1"])
        self.assertEqual(result["domains"]["visual_conclusion"]["status"],"aligned")

    def test_visual_claim_cannot_cite_transcript_as_visual_proof(self):
        claim={"claims":[{"claimKey":"visual_style","verdict":"talking_head",
                           "confidence":.9,"evidenceIds":["transcript-1"]}]}
        result=cross_validate_content_models({"qwen":claim,"deepseek":claim},{"transcript-1"},set(),
                                             ["visual_conclusion"])
        self.assertEqual(result["status"],"manual_required")
        self.assertEqual(result["commonEvidenceIds"],[])

    def test_visual_claim_requires_independent_qwen_and_kimi_evidence(self):
        claim={"claims":[{"claimKey":"visual_style","verdict":"talking_head",
                           "confidence":.9,"evidenceIds":["vq","vk"]}]}
        aligned=cross_validate_content_models(
            {"qwen":claim,"deepseek":claim},{"vq","vk"},{"vq","vk"},["visual_conclusion"],
            {"qwen":{"vq"},"kimi":{"vk"}})
        self.assertEqual(aligned["status"],"aligned")
        missing_kimi=cross_validate_content_models(
            {"qwen":claim,"deepseek":claim},{"vq","vk"},{"vq","vk"},["visual_conclusion"],
            {"qwen":{"vq"},"kimi":set()})
        self.assertEqual(missing_kimi["status"],"manual_required")

    def test_provider_failure_fails_closed(self):
        result=cross_validate_content_models({"qwen":{"claims":[]},"deepseek":"timeout"},{"e1"},set(),
                                             ["account_positioning","content_dna"])
        self.assertEqual(result["status"],"manual_required")
        self.assertEqual(result["completedProviders"],["qwen"])

    def test_builder_uses_real_database_evidence_ids(self):
        evidence=[{"id":"e1","source_id":"a1","evidence_type":"transcript","quote_text":"底盘技术解释"}]
        outputs={
            "qwen":{"claims":[
                {"claimKey":"account_positioning","verdict":"expert_education","confidence":.8,"evidenceIds":["e1"]},
                {"claimKey":"topic_focus","verdict":"technical_education","confidence":.8,"evidenceIds":["e1"]}]},
            "deepseek":{"claims":[
                {"claimKey":"account_positioning","verdict":"expert_education","confidence":.8,"evidenceIds":["e1"]},
                {"claimKey":"topic_focus","verdict":"technical_education","confidence":.8,"evidenceIds":["e1"]}]},
        }
        result=build_creator_content_validation({"display_name":"测试达人"},[],evidence,
                                                model_runner=lambda provider,prompt: outputs[provider])
        self.assertEqual(result["status"],"aligned")
        self.assertEqual(result["commonEvidenceIds"],["e1"])


if __name__ == "__main__": unittest.main()
