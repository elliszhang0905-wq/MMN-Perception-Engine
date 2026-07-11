import tempfile
import unittest
from datetime import datetime, timezone

from creator_distillation.adapters import AdapterError, DouyinAdapter, XiaohongshuAdapter
from creator_distillation.repository import CreatorRepository
from creator_distillation.scoring import score_assets, select_diverse_samples
from creator_distillation.service import CreatorDistillationService


class CreatorDistillationTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.repo=CreatorRepository(f"{self.tmp.name}/creator.db")
        self.service=CreatorDistillationService(self.repo)

    def tearDown(self): self.tmp.cleanup()

    def test_platform_link_preflight_keeps_platform_specific_capability(self):
        dy=self.service.preflight("https://www.douyin.com/user/MS4wLjAB")
        xhs=self.service.preflight("https://www.xiaohongshu.com/user/profile/abc")
        self.assertEqual(dy["platform"],"douyin")
        self.assertFalse(dy["capabilities"]["imageNote"])
        self.assertTrue(xhs["capabilities"]["imageNote"])
        with self.assertRaises(AdapterError): self.service.preflight("https://example.com/user/1")

    def test_task_defaults_to_180_days_and_50_samples(self):
        task=self.service.create_task({"creatorUrl":"https://v.douyin.com/abc/"},"org-a")
        self.assertEqual(task["range_days"],180)
        self.assertEqual(task["sample_count"],50)
        self.assertEqual(task["status"],"queued")
        self.assertIn("Celery",task["degraded_reason"])

    def test_score_is_explainable_and_noise_is_downweighted(self):
        items=[
            {"source_id":"stable","views":100000,"likes":10000,"comments":3000,"collects":2000,"shares":1000,"published_at":datetime.now(timezone.utc).isoformat(),"primary_tag":"底盘"},
            {"source_id":"noise","views":900000,"likes":30000,"comments":500,"collects":100,"shares":100,"published_at":datetime.now(timezone.utc).isoformat(),"primary_tag":"热点","interference_tags":["paid_traffic","commercial"]},
        ]
        scored=score_assets(items,followers=100000)
        stable=next(x for x in scored if x["source_id"]=="stable")
        noise=next(x for x in scored if x["source_id"]=="noise")
        self.assertTrue(stable["selection_reasons"])
        self.assertEqual(noise["sample_role"],"noise")
        self.assertGreater(stable["performance_score"],noise["performance_score"])

    def test_diverse_selection_caps_single_topic(self):
        items=[{"source_id":str(i),"primary_tag":"底盘" if i<8 else "探店"} for i in range(10)]
        selected=select_diverse_samples(items,5)
        self.assertEqual(len(selected),5)
        self.assertTrue(any(x["primary_tag"]=="探店" for x in selected))


if __name__ == "__main__": unittest.main()
