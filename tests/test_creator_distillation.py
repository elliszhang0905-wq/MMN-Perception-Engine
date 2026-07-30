import os
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch

import creator_distillation.media_processing as media_processing

from creator_distillation.adapters import (
    AdapterError, DouyinAdapter, XiaohongshuAdapter, validate_creator_identity,
)
from creator_distillation.repository import CreatorRepository
from creator_distillation.scoring import score_assets, select_diverse_samples
from creator_distillation.service import CreatorDistillationService
from creator_distillation.tasks import _run
from creator_distillation.media_processing import (
    MediaProcessingError, _safe_public_url, analyze_visual_media, parse_srt, transcribe_long_media,
)
from creator_distillation.opinion_judgment import (
    build_opinion_judgment, clean_comment_evidence, cross_validate_model_judgments,
)


class CreatorDistillationTest(unittest.TestCase):
    def test_multimodal_json_parser_uses_first_complete_object_without_crashing_job(self):
        value = media_processing._json_object(
            '说明文字 {"visual_summary":"车辆入镜","shots":[]}\n{"ignored":true}')
        self.assertEqual(value["visual_summary"], "车辆入镜")

    def test_multimodal_json_parser_normalizes_invalid_output_to_capability_error(self):
        with self.assertRaises(MediaProcessingError):
            media_processing._json_object("没有可解析的结构化结果")

    def test_ocr_json_parser_repairs_top_level_list_without_inventing_text(self):
        value = media_processing._json_object(
            '[{"imageIndex":0,"text":"报价单"}]',
            list_field="texts",
        )
        self.assertEqual(value, {"texts": [{"imageIndex": 0, "text": "报价单"}]})

    def test_visual_processing_accepts_internal_browser_frames_with_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            frame = Path(tmp) / "frame.jpg"
            frame.write_bytes(b"jpeg-frame")
            asset = {"source_id": "video-1", "media": {
                "localImagePaths": [str(frame)], "localImageTimestampsMs": [5000]
            }}
            with patch("creator_distillation.media_processing._chat_completion") as model:
                model.return_value = {"model": "test", "choices": [{"message": {"content": json.dumps({
                    "visual_summary": "第五秒出现车辆侧面",
                    "ocr_text": [],
                    "shots": [{"time_ms": 5000, "description": "车辆侧面进入画面"}],
                    "content_structure": ["产品展示"],
                    "product_entities": ["车辆"],
                    "limitations": [],
                }, ensure_ascii=False)}}]}
                evidence, mode = media_processing._run_visual_provider(
                    asset, "observer", "test", "TEST_API_KEY")
            self.assertEqual(mode, "observer")
            self.assertTrue(any(row["evidence_type"] == "shot" and row["start_ms"] == 5000 for row in evidence))
            sent = model.call_args.args[1][0]["content"]
            self.assertTrue(sent[0]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
            self.assertIn("5000ms", sent[-1]["text"])

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.repo=CreatorRepository(f"{self.tmp.name}/creator.db")
        self.service=CreatorDistillationService(self.repo)

    def tearDown(self): self.tmp.cleanup()

    def test_visual_processing_runs_independent_qwen_and_kimi_observers(self):
        calls=[]
        def fake_provider(asset,provider,model,api_key_env,base_url_env="QWEN_BASE_URL"):
            calls.append((provider,model,api_key_env,base_url_env))
            return ([{"source_id":"a1","evidence_type":"visual_summary","quote_text":provider,
                      "provenance":{"provider":provider,"model":model}}],provider)
        with patch("creator_distillation.media_processing._run_visual_provider",
                   side_effect=fake_provider):
            evidence,mode=analyze_visual_media({"source_id":"a1","media":{"videoUrl":"https://example.com/a.mp4"}})
        self.assertEqual([row[0] for row in calls],["qwen","kimi"])
        self.assertEqual({row["provenance"]["provider"] for row in evidence},{"qwen","kimi"})
        self.assertEqual(mode,"qwen+kimi")

    def test_long_asr_uses_dashscope_async_task_contract(self):
        requests=[]
        def fake_request(request,timeout,label):
            requests.append((request.full_url,request.method,dict(request.headers)))
            if request.method=="POST":
                return {"output":{"task_id":"task-1"}}
            return {"output":{"task_status":"SUCCEEDED","result":{"transcription":"长视频真实转写"}}}
        with patch.dict(os.environ,{"MMN_CREATOR_ASR_FILETRANS_API_KEY":"test-only-key"}), \
             patch("creator_distillation.media_processing._request_json",side_effect=fake_request), \
             patch("creator_distillation.media_processing._safe_public_url",side_effect=lambda value:value):
            text,model=transcribe_long_media("https://example.com/long.mp4",360000)
        self.assertEqual(text,"长视频真实转写")
        self.assertEqual(model,"qwen3-asr-flash-filetrans")
        self.assertTrue(requests[0][0].endswith("/services/audio/asr/transcription"))
        self.assertTrue(requests[1][0].endswith("/tasks/task-1"))
        self.assertEqual(requests[0][2].get("X-dashscope-async"),"enable")

    def test_transcribe_media_reads_legacy_top_level_duration_for_long_video(self):
        asset = {
            "source_id": "long-video",
            "duration_ms": 360000,
            "media": {"audioUrl": "https://example.com/long.mp4"},
        }
        with patch(
            "creator_distillation.media_processing.transcribe_long_media",
            return_value=("长视频真实转写", "filetrans-test"),
        ) as long_asr:
            evidence, mode = media_processing.transcribe_media(asset)
        long_asr.assert_called_once_with("https://example.com/long.mp4", 360000)
        self.assertEqual(mode, "qwen3_asr_filetrans")
        self.assertEqual(evidence[0]["quote_text"], "长视频真实转写")

    def test_platform_link_preflight_keeps_platform_specific_capability(self):
        dy=self.service.preflight("https://www.douyin.com/user/MS4wLjAB")
        xhs=self.service.preflight("https://www.xiaohongshu.com/user/profile/abc")
        self.assertEqual(dy["platform"],"douyin")
        self.assertFalse(dy["capabilities"]["imageNote"])
        self.assertTrue(xhs["capabilities"]["imageNote"])
        with self.assertRaises(AdapterError): self.service.preflight("https://example.com/user/1")

    def test_douyin_short_link_normalizes_iesdouyin_share_url(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self,*_): return False
            def geturl(self):
                return "https://www.iesdouyin.com/share/user/SEC-USER-1?sec_uid=SEC-USER-1"

        with patch("creator_distillation.adapters.urlopen",return_value=FakeResponse()):
            reference=DouyinAdapter().creator_reference("https://v.douyin.com/abc/")

        self.assertEqual(reference["resolvedUrl"],"https://www.douyin.com/user/SEC-USER-1")
        self.assertEqual(reference["secUserId"],"SEC-USER-1")

    def test_task_defaults_to_180_days_and_50_samples(self):
        task=self.service.create_task({"creatorUrl":"https://v.douyin.com/abc/",
                                       "expectedCreatorName":"测试达人"},"org-a")
        self.assertEqual(task["range_days"],180)
        self.assertEqual(task["sample_count"],50)
        self.assertEqual(task["status"],"queued")
        self.assertIn("Celery",task["degraded_reason"])

    def test_identical_active_task_is_reused_before_paid_collection(self):
        payload={"creatorUrl":"https://www.douyin.com/user/sec-reuse",
                 "expectedCreatorName":"复用达人","sampleCount":50}
        first=self.service.create_task(payload,"org-a")
        second=self.service.create_task(payload,"org-a")
        self.assertEqual(first["id"],second["id"])
        self.assertTrue(second["reused"])
        self.assertEqual(len(self.repo.list_tasks("org-a")),1)

    def test_adapter_stops_before_exceeding_request_attempt_budget(self):
        with patch.dict(os.environ,{"TIKHUB_API_KEY":"test-only","MMN_CREATOR_REQUEST_ATTEMPT_BUDGET":"2"}), \
             patch("creator_distillation.adapters.urlopen",side_effect=URLError("timeout")) as request, \
             patch("creator_distillation.adapters.time.sleep"):
            adapter=DouyinAdapter()
            with self.assertRaises(AdapterError) as ctx:
                adapter.request("profile",{"sec_user_id":"sec-a"},attempts=4)
        self.assertEqual(ctx.exception.category,"request_budget_exhausted")
        self.assertEqual(request.call_count,2)

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

    def test_tikhub_business_error_does_not_become_empty_data(self):
        with self.assertRaises(AdapterError) as ctx:
            DouyinAdapter.ensure_success({"code": 400, "message_zh": "参数错误"}, "/profile")
        self.assertEqual(ctx.exception.category, "provider_business_error")

    def test_identity_gate_rejects_provider_id_or_name_mismatch(self):
        creator={"platform_creator_id":"wrong-sec","display_name":"错误账号","profile":{}}
        with self.assertRaises(AdapterError) as ctx:
            validate_creator_identity(creator,{"secUserId":"expected-sec"},"目标达人")
        self.assertEqual(ctx.exception.category,"identity_mismatch")

    def test_identity_gate_permanently_blocks_songzhen(self):
        creator={"platform_creator_id":"MS4wLjABAAAANXSltcLCzDGmdNFI2Q_QixVTr67NiYzjKOIP5s03CAE",
                 "display_name":"songzhen","profile":{}}
        with self.assertRaises(AdapterError) as ctx:
            validate_creator_identity(creator,expected_name="songzhen")
        self.assertEqual(ctx.exception.category,"creator_blocked")

    def test_blocked_creator_response_cannot_persist_any_profile(self):
        task=self.repo.create_task("org-a","https://www.douyin.com/user/blocked","douyin",180,20,
                                   {"expectedCreatorName":"目标达人"})

        class MismatchedAdapter:
            version="v1"
            def collect_creator(self,url,max_posts):
                return ({"platform":"douyin",
                         "platform_creator_id":"MS4wLjABAAAANXSltcLCzDGmdNFI2Q_QixVTr67NiYzjKOIP5s03CAE",
                         "display_name":"songzhen","profile":{}},
                        [{"source_id":"should-not-persist"}],[])

        with patch.dict(os.environ,{"MMN_CREATOR_DB_PATH":str(self.repo.path)}), \
             patch("creator_distillation.tasks.DouyinAdapter",MismatchedAdapter):
            result=_run(task["id"])
        self.assertEqual(result["status"],"failed")
        self.assertEqual(result["error_category"],"creator_blocked")
        self.assertEqual(self.repo.list_creators("org-a"),[])

    def test_douyin_profile_and_posts_normalize_provenance_and_missing_views(self):
        adapter=DouyinAdapter()
        profile=adapter.normalize_profile({"data":{"user":{"nickname":"测试达人","sec_uid":"sec-1",
                    "uid":"uid-1","follower_count":1234}}},"/profile",{"sourceUrl":"https://douyin.com/user/sec-1",
                    "resolvedUrl":"https://douyin.com/user/sec-1","secUserId":"sec-1"})
        self.assertEqual(profile["platform_creator_id"],"sec-1")
        self.assertEqual(profile["profile"]["followers"]["value"],1234)
        posts=adapter.normalize_posts({"data":{"aweme_list":[{"aweme_id":"post-1","desc":"真实样本",
                    "create_time":1700000000,"statistics":{"play_count":0,"digg_count":99,"comment_count":8,
                    "share_count":3}}]}},"/posts")
        self.assertEqual(len(posts),1)
        self.assertIsNone(posts[0]["views"])
        self.assertIn("views",posts[0]["provenance"]["missingMetrics"])
        self.assertEqual(posts[0]["likes"],99)
        comments=adapter.normalize_comments({"data":{"comments":[{"cid":"comment-1","text":"车内空间不错",
                    "digg_count":12,"user":{"nickname":"公开用户"}}]}},"/comments","post-1")
        self.assertEqual(comments[0]["source_id"],"post-1")
        self.assertEqual(comments[0]["quote_text"],"车内空间不错")
        self.assertEqual(comments[0]["metadata"]["likes"],12)

    def test_xiaohongshu_app_v2_normalizes_profile_notes_and_comments(self):
        adapter=XiaohongshuAdapter()
        envelope=lambda data: {"code":200,"data":{"code":0,"success":True,"data":data}}
        reference={"sourceUrl":"https://www.xiaohongshu.com/user/profile/user-1",
                   "resolvedUrl":"https://www.xiaohongshu.com/user/profile/user-1",
                   "userId":"user-1","xsecToken":""}
        profile=adapter.normalize_profile(envelope({"userid":"user-1","nickname":"测试博主","fans":321,
                    "follows":12,"desc":"汽车工程师","note_num_stat":{"posted":9,"liked":100,"collected":50}}),
                    "/profile",reference)
        self.assertEqual(profile["platform_creator_id"],"user-1")
        self.assertEqual(profile["profile"]["followers"]["value"],321)
        notes=adapter.normalize_posts(envelope({"notes":[{"id":"note-1","display_title":"底盘解析",
                    "type":"video","likes":88,"comments_count":7,"collected_count":15,
                    "share_count":3,"view_count":0,"create_time":1700000000}]}),"/posts")
        self.assertEqual(notes[0]["asset_type"],"video")
        self.assertIsNone(notes[0]["views"])
        self.assertEqual(notes[0]["collects"],15)
        comments=adapter.normalize_comments(envelope({"comments":[{"id":"comment-1","content":"讲得很清楚",
                    "like_count":6,"user":{"nickname":"公开用户","userid":"public-1"}}]}),"/comments","note-1")
        self.assertEqual(comments[0]["quote_text"],"讲得很清楚")
        self.assertEqual(comments[0]["metadata"]["likes"],6)

    def test_xiaohongshu_nested_business_error_is_rejected(self):
        with self.assertRaises(AdapterError) as ctx:
            XiaohongshuAdapter.ensure_success({"code":200,"data":{"code":-1,"success":False,
                                                    "msg":"账号不可访问"}},"/profile")
        self.assertEqual(ctx.exception.category,"provider_business_error")

    def test_srt_transcript_keeps_timestamps_and_source_identity(self):
        evidence=parse_srt("1\n00:00:01,250 --> 00:00:03,500\n底盘很整\n\n"
                           "2\n00:00:03,500 --> 00:00:05,000\n滤振清晰\n","note-1")
        self.assertEqual(len(evidence),2)
        self.assertEqual(evidence[0]["start_ms"],1250)
        self.assertEqual(evidence[0]["end_ms"],3500)
        self.assertEqual(evidence[0]["evidence_type"],"transcript")
        self.assertEqual(evidence[0]["source_id"],"note-1")

    def test_media_url_guard_allows_proxy_mapped_platform_cdn_but_rejects_private_host(self):
        fake_dns=lambda host,port: [(2,1,6,"",("198.18.0.51",port))]
        with patch("creator_distillation.media_processing.socket.getaddrinfo",fake_dns):
            self.assertEqual(_safe_public_url("https://sns-i11.rednotecdn.com/a.jpg"),
                             "https://sns-i11.rednotecdn.com/a.jpg")
            self.assertEqual(
                _safe_public_url(
                    "https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/transcript.json"
                ),
                "https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/transcript.json",
            )
            with self.assertRaises(MediaProcessingError):
                _safe_public_url("https://untrusted.example/a.jpg")

    def test_douyin_and_xiaohongshu_notes_keep_ephemeral_media_for_processing(self):
        douyin=DouyinAdapter().normalize_posts({"data":{"aweme_list":[{"aweme_id":"post-media",
                 "aweme_type":68,"desc":"图文","images":[{"url_list":["https://img.example/a.jpg"]}],
                 "video":{"play_addr":{"url_list":["https://audio.example/a.mp3"]}},
                 "statistics":{"digg_count":1}}]}},"/posts")[0]
        self.assertEqual(douyin["media"]["imageUrls"],["https://img.example/a.jpg"])
        self.assertEqual(douyin["media"]["audioUrl"],"https://audio.example/a.mp3")
        envelope={"code":200,"data":{"code":0,"success":True,"data":{"notes":[{
                 "id":"note-media","type":"video","title":"视频","images_list":[],
                 "video_info_v2":{"capa":{"duration":30},"media":{"stream":{"h264":[{
                 "master_url":"https://video.example/a.mp4"}]},"video":{"subtitles":{"source":[{
                 "url":"https://subtitle.example/a.srt"}]}}}}}]} }}
        xhs=XiaohongshuAdapter().normalize_posts(envelope,"/posts")[0]
        self.assertEqual(xhs["media"]["videoUrl"],"https://video.example/a.mp4")
        self.assertEqual(xhs["media"]["subtitleUrls"],["https://subtitle.example/a.srt"])
        self.assertEqual(xhs["media"]["durationMs"],30000)

    def test_comment_collection_enforces_local_limits_when_provider_returns_more(self):
        adapter=DouyinAdapter()
        adapter.request=lambda name,params: ({"code":200,"data":{"comments":[
            {"cid":"c1","text":"评论1"},{"cid":"c2","text":"评论2"}]}},
            {"endpoint":"/comments","status":200})
        evidence,exchanges=adapter.collect_comments([{"source_id":"post-1"},{"source_id":"post-2"}],
                                                    max_assets=1,comments_per_asset=1)
        self.assertEqual(len(exchanges),1)
        self.assertEqual([x["comment_id"] for x in evidence],["c1"])

    def test_missing_views_use_relative_interactions_instead_of_fake_zero_rate(self):
        items=[
            {"source_id":"strong","views":None,"likes":1000,"comments":100,"shares":50,
             "published_at":datetime.now(timezone.utc).isoformat()},
            {"source_id":"weak","views":None,"likes":10,"comments":1,"shares":0,
             "published_at":datetime.now(timezone.utc).isoformat()},
        ]
        scored=score_assets(items,followers=None)
        self.assertEqual(scored[0]["source_id"],"strong")
        self.assertEqual(scored[0]["scoring_mode"],"interaction_relative")
        self.assertTrue(any("播放量缺失" in reason for reason in scored[0]["selection_reasons"]))

    def test_collection_persistence_is_idempotent_and_keeps_null_metrics(self):
        task=self.repo.create_task("org-a","https://www.douyin.com/user/sec-1","douyin",180,20,
                                   {"expectedCreatorName":"测试达人"})
        creator={"platform":"douyin","platform_creator_id":"sec-1","display_name":"测试达人",
                 "profile":{"identity":{"status":"needs_review"},"provenance":{"sourceEndpoint":"/profile"}}}
        assets=[{"source_id":"post-1","asset_type":"video","title":"测试作品","views":None,"likes":99,
                 "comments":8,"collects":None,"shares":3,"performance_score":88.0,"sample_role":"stable",
                 "capabilities":{"metadata":True,"comments":True,"transcript":True,"ocr":True,"visual":True},
                 "provenance":{"sourceEndpoint":"/posts","missingMetrics":["views","collects"]}}]
        evidence=[{"source_id":"post-1","comment_id":"comment-1","evidence_type":"comment",
                   "quote_text":"真实用户评论","confidence":.95,"provenance":{"sourceEndpoint":"/comments"}},
                  {"source_id":"post-1","comment_id":"media:transcript:0","evidence_type":"transcript",
                   "start_ms":100,"end_ms":900,"quote_text":"真实字幕","confidence":.98,
                   "provenance":{"processor":"platform_subtitle"}}]
        first=self.repo.save_collection(task,creator,assets,evidence)
        second=self.repo.save_collection(task,creator,assets,evidence)
        self.assertEqual(first["inserted"],1)
        self.assertEqual(second["updated"],1)
        detail=self.repo.creator_detail(first["creatorId"])
        self.assertEqual(len(detail["assets"]),1)
        self.assertIsNone(detail["assets"][0]["metrics"]["views"])
        self.assertEqual(detail["profile"]["status"],"needs_review")
        asset_detail=self.repo.asset_detail(detail["assets"][0]["id"])
        self.assertEqual(len(asset_detail["evidence"]),2)
        transcript=next(x for x in asset_detail["evidence"] if x["evidence_type"]=="transcript")
        self.assertEqual(transcript["start_ms"],100)
        self.assertTrue(asset_detail["asset"]["capabilities"]["visual"])
        self.assertEqual(first["evidenceInserted"],2)
        self.assertEqual(second["evidenceUpdated"],2)

    def test_single_asset_media_action_persists_capabilities_without_touching_comments(self):
        task=self.repo.create_task("org-a","https://www.douyin.com/user/sec-1","douyin",180,20,{})
        creator={"platform":"douyin","platform_creator_id":"sec-1","display_name":"测试达人","profile":{}}
        assets=[{"source_id":"post-media","asset_type":"video","title":"待补媒体证据",
                 "performance_score":80,"provenance":{},
                 "media":{"videoUrl":"https://v.douyinvod.com/video.mp4","imageUrls":[]}}]
        comments=[{"source_id":"post-media","comment_id":"comment-keep","evidence_type":"comment",
                   "quote_text":"保留的评论","confidence":.95,"provenance":{"sourceEndpoint":"/comments"}}]
        saved=self.repo.save_collection(task,creator,assets,comments)
        asset_id=saved["assetIds"][0]
        generated=[
            {"source_id":"post-media","comment_id":"media:transcript:0","evidence_type":"transcript",
             "quote_text":"真实转写","confidence":.9,"provenance":{"processor":"test_asr"}},
            {"source_id":"post-media","comment_id":"media:ocr:0","evidence_type":"ocr",
             "quote_text":"画面文字","confidence":.82,"provenance":{"processor":"test_vl"}},
            {"source_id":"post-media","comment_id":"media:shot:0","evidence_type":"shot",
             "quote_text":"车辆特写","confidence":.8,"provenance":{"processor":"test_vl"}},
            {"source_id":"post-media","comment_id":"media:visual:summary","evidence_type":"visual_summary",
             "quote_text":"城市道路场景","confidence":.85,"provenance":{"processor":"test_vl"}},
        ]
        with patch("creator_distillation.service.process_representative_media",
                   return_value=(generated,{"processedAssetCount":1},[])):
            result=self.service.handle_post(
                f"/api/creator-distillation/assets/{asset_id}/media",{},"org-a"
            )
        self.assertEqual(result["status"],"available")
        self.assertTrue(result["asset"]["capabilities"]["ocr"])
        self.assertTrue(result["asset"]["capabilities"]["visual"])
        self.assertEqual(result["asset"]["analysis"]["mediaProcessing"]["status"],"available")
        self.assertEqual(result["asset"]["analysis"]["media"]["videoUrl"],
                         "https://v.douyinvod.com/video.mp4")
        self.assertEqual(sum(item["evidence_type"]=="comment" for item in result["evidence"]),1)
        self.assertEqual(sum(item["evidence_type"]!="comment" for item in result["evidence"]),4)
        refreshed_creator=self.repo.creator_detail(saved["creatorId"])
        self.assertIn("4 条内容证据",refreshed_creator["profile"]["dna"]["summary"])
        self.assertEqual(len(refreshed_creator["profile"]["dna"]["mediaEvidence"]),4)
        with self.assertRaises(KeyError):
            self.service.handle_post(f"/api/creator-distillation/assets/{asset_id}/media",{},"org-b")

    def test_single_asset_media_action_records_provider_failure_for_the_ui(self):
        task=self.repo.create_task("org-a","https://www.douyin.com/user/sec-1","douyin",180,20,{})
        saved=self.repo.save_collection(
            task,{"platform":"douyin","platform_creator_id":"sec-1","display_name":"测试达人","profile":{}},
            [{"source_id":"post-no-media","title":"无媒体地址","performance_score":70,"provenance":{}}],[],
        )
        asset_id=saved["assetIds"][0]
        with patch("creator_distillation.service.DouyinAdapter.collect_creator",
                   side_effect=AdapterError("平台暂时不可用","provider_timeout",True,True)):
            result=self.service.handle_post(
                f"/api/creator-distillation/assets/{asset_id}/media",{},"org-a"
            )
        self.assertEqual(result["status"],"failed")
        self.assertIn("平台暂时不可用",result["message"])
        self.assertEqual(result["asset"]["analysis"]["mediaProcessing"]["status"],"failed")

    def test_task_run_completes_metadata_collection_and_exposes_review_asset(self):
        task=self.repo.create_task("org-a","https://www.douyin.com/user/sec-1","douyin",180,20,
                                   {"expectedCreatorName":"测试达人"})

        class FakeDouyinAdapter:
            version="v1"
            def collect_creator(self,url,max_posts):
                creator={"platform":"douyin","platform_creator_id":"sec-1","display_name":"测试达人",
                         "followers":None,"profile":{"identity":{"status":"needs_review"},
                         "provenance":{"sourceEndpoint":"/profile"}}}
                assets=[{"source_id":"post-1","asset_type":"video","title":"测试作品","views":None,
                         "likes":99,"comments":8,"collects":None,"shares":3,"published_at":datetime.now(timezone.utc).isoformat(),
                         "primary_tag":"汽车","interference_tags":[],"provenance":{"sourceEndpoint":"/posts",
                         "missingMetrics":["views","collects"]}}]
                return creator,assets,[({"code":200,"data":{}},{"endpoint":"/profile","status":200}),
                                      ({"code":200,"data":{}},{"endpoint":"/posts","status":200})]
            def collect_comments(self,assets,max_assets,comments_per_asset):
                evidence=[{"source_id":"post-1","comment_id":"comment-1","evidence_type":"comment",
                           "quote_text":"真实用户评论","confidence":.95,"provenance":{"sourceEndpoint":"/comments"}}]
                return evidence,[({"code":200,"data":{}},{"endpoint":"/comments","status":200})]

        with patch.dict(os.environ,{"MMN_CREATOR_DB_PATH":str(self.repo.path)}), \
             patch("creator_distillation.tasks.DouyinAdapter",FakeDouyinAdapter):
            result=_run(task["id"])
        self.assertEqual(result["status"],"completed")
        self.assertEqual(result["stage"],"review")
        creator_id=result["capabilities"]["creatorId"]
        detail=self.repo.creator_detail(creator_id)
        self.assertEqual(detail["creator"]["display_name"],"测试达人")
        self.assertEqual(len(detail["assets"]),1)
        self.assertEqual(result["capabilities"]["commentEvidenceCount"],1)
        self.assertEqual(detail["profile"]["dna"]["generationMode"],"deterministic_content_evidence_index")
        self.assertEqual(detail["profile"]["status"],"needs_review")
        self.assertIn("等待提炼",detail["creator"]["profile"]["summary"])
        self.assertNotIn("audienceLanguage",detail["profile"]["dna"])

    def test_xiaohongshu_task_run_completes_notes_and_comment_evidence(self):
        task=self.repo.create_task("org-a","https://www.xiaohongshu.com/user/profile/user-1",
                                   "xiaohongshu",180,20,{"expectedCreatorName":"测试博主"})

        class FakeXiaohongshuAdapter:
            version="v1"
            def collect_creator(self,url,max_posts):
                creator={"platform":"xiaohongshu","platform_creator_id":"user-1",
                         "display_name":"测试博主","followers":321,
                         "profile":{"identity":{"status":"needs_review"},
                                    "provenance":{"sourceEndpoint":"/profile"}}}
                assets=[{"source_id":"note-1","asset_type":"image_note","title":"底盘解析",
                         "views":None,"likes":88,"comments":7,"collects":15,"shares":3,
                         "published_at":datetime.now(timezone.utc).isoformat(),"primary_tag":"汽车",
                         "interference_tags":[],"provenance":{"sourceEndpoint":"/posts",
                         "missingMetrics":["views"]}}]
                return creator,assets,[({"code":200,"data":{}},{"endpoint":"/profile","status":200}),
                                      ({"code":200,"data":{}},{"endpoint":"/posts","status":200})]
            def collect_comments(self,assets,max_assets,comments_per_asset):
                evidence=[{"source_id":"note-1","comment_id":"comment-1","evidence_type":"comment",
                           "quote_text":"真实小红书评论","confidence":.95,
                           "provenance":{"sourceEndpoint":"/comments"}}]
                return evidence,[({"code":200,"data":{}},{"endpoint":"/comments","status":200})]

        with patch.dict(os.environ,{"MMN_CREATOR_DB_PATH":str(self.repo.path)}), \
             patch("creator_distillation.tasks.XiaohongshuAdapter",FakeXiaohongshuAdapter):
            result=_run(task["id"])
        self.assertEqual(result["status"],"completed")
        self.assertEqual(result["stage"],"review")
        self.assertEqual(result["capabilities"]["commentEvidenceCount"],1)
        detail=self.repo.creator_detail(result["capabilities"]["creatorId"])
        self.assertEqual(detail["creator"]["platform"],"xiaohongshu")
        self.assertEqual(detail["assets"][0]["asset_type"],"image_note")

    def test_comment_cleaning_filters_bot_prompt_and_deduplicates_user(self):
        rows=[
            {"id":"e1","comment_id":"c1","source_id":"a1","quote_text":"@问一问 总结一下视频内容",
             "provenance":{"metadata":{"userId":"bot"}}},
            {"id":"e2","comment_id":"c2","source_id":"a1","quote_text":"两吨多的车用255轮胎是不是窄了？",
             "provenance":{"metadata":{"userId":"u1","likes":12}}},
            {"id":"e3","comment_id":"c3","source_id":"a1","quote_text":"两吨多的车用255轮胎是不是窄了？",
             "provenance":{"metadata":{"userId":"u1","likes":8}}},
        ]
        cleaned,rejected=clean_comment_evidence(rows)
        self.assertEqual([row["evidenceId"] for row in cleaned],["e2"])
        self.assertEqual(rejected["noise"],1)
        self.assertEqual(rejected["duplicate"],1)
        self.assertEqual(cleaned[0]["issueKeys"],["tire_matching"])

    def test_opinion_signal_is_scoped_and_keeps_fact_inference_boundary(self):
        rows=[{"id":f"e{i}","comment_id":f"c{i}","source_id":f"a{i}",
               "quote_text":"这台车的轮胎匹配是不是偏窄，担心安全余量？",
               "provenance":{"metadata":{"userId":f"u{i}","likes":i}}} for i in range(1,4)]
        result=build_opinion_judgment(rows,asset_count=10,use_models=False)
        self.assertEqual(result["scope"],"platform_candidate")
        self.assertEqual(result["status"],"manual_required")
        self.assertEqual(result["issueSignals"][0]["opinionCount"],3)
        self.assertEqual(result["completeness"]["worksCovered"],3)
        self.assertIn("fact",result["statementBoundary"])
        self.assertIn("不能直接发布",result["limitations"][-1])

    def test_dual_model_gate_keeps_only_common_evidence_and_direction(self):
        outputs={
            "qwen":{"issues":[{"issueKey":"tire_matching","direction":"concern",
                                  "confidence":.82,"evidenceIds":["e1","e2"]}]},
            "deepseek":{"issues":[{"issueKey":"tire_matching","direction":"concern",
                                     "confidence":.76,"evidenceIds":["e2","e3"]}]},
        }
        checked=cross_validate_model_judgments(outputs,{"e1","e2","e3"})
        self.assertEqual(checked["status"],"aligned")
        self.assertEqual(checked["commonEvidenceIds"],["e2"])
        conflicted={**outputs,"deepseek":{"issues":[{"issueKey":"tire_matching","direction":"praise",
                                                        "confidence":.9,"evidenceIds":["e2"]}]}}
        self.assertEqual(cross_validate_model_judgments(conflicted,{"e2"})["status"],"manual_required")

    def test_opinion_judgment_is_versioned_separately_from_content_profile(self):
        task=self.repo.create_task("org-a","https://www.douyin.com/user/sec-1","douyin",180,20,{})
        creator={"platform":"douyin","platform_creator_id":"sec-1","display_name":"测试达人","profile":{}}
        assets=[{"source_id":"post-1","title":"轮胎解析","performance_score":80,"provenance":{}}]
        evidence=[{"source_id":"post-1","comment_id":"c1","evidence_type":"comment",
                   "quote_text":"轮胎是不是偏窄？","confidence":.95,
                   "provenance":{"metadata":{"userId":"u1"}}}]
        saved=self.repo.save_collection(task,creator,assets,evidence)
        inputs=self.repo.creator_opinion_inputs(saved["creatorId"])
        judgment=build_opinion_judgment(inputs["comments"],inputs["assetCount"],use_models=False)
        first=self.repo.save_opinion_judgment(saved["creatorId"],judgment)
        second=self.repo.save_opinion_judgment(saved["creatorId"],judgment)
        detail=self.repo.creator_detail(saved["creatorId"])
        self.assertEqual(first["version"],1)
        self.assertEqual(second["version"],2)
        self.assertEqual(detail["opinionJudgment"]["version"],2)
        self.assertNotIn("opinionJudgment",detail["profile"]["dna"])

    def test_same_platform_asset_is_isolated_between_organizations(self):
        creator={"platform":"douyin","platform_creator_id":"sec-shared","display_name":"同一达人","profile":{}}
        assets=[{"source_id":"post-shared","title":"同一公开作品","performance_score":80,"provenance":{}}]
        task_a=self.repo.create_task("org-a","https://www.douyin.com/user/sec-shared","douyin",180,20,{})
        task_b=self.repo.create_task("org-b","https://www.douyin.com/user/sec-shared","douyin",180,20,{})
        saved_a=self.repo.save_collection(task_a,creator,assets,[])
        saved_b=self.repo.save_collection(task_b,creator,assets,[])

        self.assertNotEqual(saved_a["creatorId"],saved_b["creatorId"])
        self.assertNotEqual(saved_a["assetIds"],saved_b["assetIds"])
        self.assertEqual(self.repo.asset_detail(saved_a["assetIds"][0],"org-a")["asset"]["org_id"],"org-a")
        self.assertEqual(self.repo.asset_detail(saved_b["assetIds"][0],"org-b")["asset"]["org_id"],"org-b")
        with self.assertRaises(KeyError):
            self.repo.asset_detail(saved_a["assetIds"][0],"org-b")

    def test_task_creator_and_opinion_actions_reject_cross_org_ids(self):
        task=self.repo.create_task("org-a","https://www.douyin.com/user/sec-a","douyin",180,20,{})
        saved=self.repo.save_collection(
            task,
            {"platform":"douyin","platform_creator_id":"sec-a","display_name":"组织A达人","profile":{}},
            [{"source_id":"post-a","title":"组织A作品","performance_score":80,"provenance":{}}],
            [],
        )
        creator_id=saved["creatorId"]

        self.assertIsNone(self.repo.get_task(task["id"],"org-b"))
        with self.assertRaises(KeyError):
            self.service.handle_get(f"/api/creator-distillation/creators/{creator_id}",{},"org-b")
        with self.assertRaises(KeyError):
            self.service.handle_post(f"/api/creator-distillation/tasks/{task['id']}/pause",{},"org-b")
        with self.assertRaises(KeyError):
            self.service.handle_post(f"/api/creator-distillation/tasks/{task['id']}/retry",{},"org-b")
        with self.assertRaises(KeyError):
            self.service.handle_post(
                f"/api/creator-distillation/creators/{creator_id}/opinion-judgment",{},"org-b"
            )

    def test_methodology_assets_are_scoped_by_organization(self):
        with self.repo.connect() as conn:
            conn.execute(
                "insert into methodology_assets values(?,?,?,?,?,?,?,?,?)",
                ("method-a","org-a","opening","A方法","{}","[]","[]","2026-07-29","2026-07-29"),
            )
            conn.execute(
                "insert into methodology_assets values(?,?,?,?,?,?,?,?,?)",
                ("method-b","org-b","opening","B方法","{}","[]","[]","2026-07-29","2026-07-29"),
            )
        self.assertEqual([row["id"] for row in self.repo.methodologies("org-a")],["method-a"])
        self.assertEqual([row["id"] for row in self.repo.methodologies("org-b")],["method-b"])

    def test_legacy_asset_schema_migrates_without_losing_rows(self):
        legacy_path=Path(self.tmp.name)/"legacy.db"
        with sqlite3.connect(legacy_path) as conn:
            conn.executescript("""
            create table creators(id text primary key, org_id text, platform text, platform_creator_id text,
              display_name text, profile_json text, created_at text, updated_at text);
            create table assets(id text primary key, creator_id text, task_id text, platform text, asset_type text,
              source_id text, source_url text, title text, published_at text, metrics_json text, provenance_json text,
              analysis_json text, performance_score real, sample_role text, capabilities_json text,
              degraded_reason text, created_at text, updated_at text, unique(platform,source_id));
            create table methodology_assets(id text primary key, methodology_type text, title text, body_json text,
              source_creator_ids_json text, evidence_ids_json text, created_at text, updated_at text);
            insert into creators values('creator-a','org-a','douyin','sec-a','达人A','{}','t','t');
            insert into assets values('asset-a','creator-a','task-a','douyin','video','post-a','','作品A','',
              '{}','{}','{}',80,'stable','{}','','t','t');
            insert into methodology_assets values('method-legacy','opening','旧方法','{}','[]','[]','t','t');
            """)

        migrated=CreatorRepository(legacy_path)
        self.assertEqual(migrated.asset_detail("asset-a","org-a")["asset"]["org_id"],"org-a")
        self.assertEqual([row["id"] for row in migrated.methodologies("legacy-unscoped")],["method-legacy"])


if __name__ == "__main__": unittest.main()
