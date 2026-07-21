import unittest

import server


class VerticalRankLearningTest(unittest.TestCase):
    def setUp(self):
        self.context = {
            "model": "奥迪E7X",
            "platform": "懂车帝",
            "period": "6.25-7.1",
            "source": "懂车帝正反向排名.xlsx",
            "rows": [
                {"competitor": "奔驰GLC EV", "positiveRank": 1, "negativeRank": 3, "share": 0.24, "status": "正向关注强"},
                {"competitor": "宝马iX3", "positiveRank": 2, "negativeRank": 1, "share": 0.19, "status": "高关注高对比"},
            ],
        }

    @staticmethod
    def response(provider):
        if provider == "fusion":
            return "\n\n".join([
                "### 一句话判断", "E7X应先化解豪华与新势力双重对比压力。",
                "### 为什么会这样", "三路分析共同指向两类核心参照，但用户动机仍需验证。",
                "### 关键竞品关系", "奔驰GLC EV与宝马iX3构成当前重点参照。",
                "### 下一步打法", "建立同场景差异证据，并跟踪下一周期排名。",
                "### RAG入库卡片", "E7X正反向竞争格局融合学习卡。",
            ])
        labels = {"qwen": "先处理反向牵引", "deepseek": "先锁定正向参照", "kimi": "先验证竞品关系"}
        return "\n\n".join([
            "### 一句话判断", labels[provider],
            "### 为什么会这样", "只依据锁定排名判断。",
            "### 关键竞品关系", "宝马iX3反向排名第一。",
            "### 下一步打法", "验证差异表达。",
            "### RAG入库卡片", "正反向关系学习卡。",
        ])

    def test_three_independent_analyses_unlock_rag_persistence(self):
        result = server.run_vertical_rank_learning(
            self.context, provider_runner=lambda provider, _prompt: self.response(provider)
        )
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["canPersist"])
        self.assertEqual(result["statusLabel"], "三路分析已融合为一个结论")
        self.assertIn("E7X应先化解豪华与新势力双重对比压力", result["text"])
        self.assertNotIn("独立判断", result["text"])
        self.assertEqual(result["analysisChecks"]["fusion"], "completed")

    def test_one_failed_analysis_keeps_rag_gate_closed(self):
        def runner(provider, _prompt):
            if provider == "kimi":
                raise RuntimeError("provider secret")
            return self.response(provider)

        result = server.run_vertical_rank_learning(self.context, provider_runner=runner)
        self.assertEqual(result["status"], "degraded")
        self.assertFalse(result["canPersist"])
        self.assertEqual(result["errors"], {"flagshipC": "当前独立分析通道未完成"})
        self.assertNotIn("provider secret", str(result))
        self.assertIn("仅完成2/3", result["statusLabel"])

    def test_fusion_failure_keeps_rag_gate_closed(self):
        result = server.run_vertical_rank_learning(
            self.context,
            provider_runner=lambda provider, _prompt: (
                "只有一句话，没有融合结构" if provider == "fusion" else self.response(provider)
            ),
        )
        self.assertEqual(result["status"], "degraded")
        self.assertFalse(result["canPersist"])
        self.assertEqual(result["analysisChecks"]["fusion"], "unavailable")
        self.assertEqual(result["errors"], {"fusion": "三路分析已完成，但融合裁决未完成"})

    def test_fingerprint_changes_with_locked_rank_data(self):
        first = server.vertical_learning_fingerprint(self.context)
        changed = {**self.context, "rows": [{**self.context["rows"][0], "negativeRank": 2}]}
        self.assertNotEqual(first, server.vertical_learning_fingerprint(changed))


if __name__ == "__main__":
    unittest.main()
