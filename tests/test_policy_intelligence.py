import json
import sqlite3
import unittest


from policy_intelligence import (
    EVAL_FIELDS,
    SUPPORTED_POLICY_REGIONS,
    build_policy_dashboard_payload,
    build_sales_warning_policy_profiles,
    build_vehicle_policy_impact,
    cross_validate_policy_strategies,
    evaluate_policy_analysis,
    fetch_policy_source,
    init_policy_schema,
    normalize_policy_json,
    parse_policy_with_gateway,
    review_policy,
    save_policy_document,
    save_policy_record,
    seed_policy_mvp,
    seed_policy_sources,
    validate_source_url,
)
from group_dashboard import load_sales_warning


OFFICIAL_SOURCE = {
    "id": "mofcom",
    "name": "商务部",
    "level": 1,
    "baseUrl": "https://www.mofcom.gov.cn",
    "url": "https://www.mofcom.gov.cn/zfxxgk/example.html",
}


class PolicySchemaTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_policy_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_schema_creates_traceable_policy_layers(self):
        tables = {
            row[0]
            for row in self.conn.execute("select name from sqlite_master where type='table'")
        }
        self.assertTrue(
            {
                "policy_sources",
                "policy_documents",
                "policy_records",
                "policy_reviews",
                "policy_analysis_results",
                "policy_evaluations",
                "policy_fetch_runs",
            }.issubset(tables)
        )

    def test_source_registry_keeps_authority_levels_distinct(self):
        saved = seed_policy_sources(self.conn)
        levels = {
            row["name"]: row["source_level"]
            for row in self.conn.execute("select name, source_level from policy_sources")
        }
        self.assertGreaterEqual(saved, 8)
        self.assertEqual(levels["商务部"], 1)
        self.assertEqual(levels["地方政府官网"], 2)
        self.assertEqual(levels["乘联会"], 3)

    def test_sales_warning_policy_profiles_follow_selected_models_dynamic_peer_pool(self):
        warning = load_sales_warning(path="data/dongchedi_sales/sales_warning_latest.json")
        own = next(item for item in warning["saicModels"] if item["model"] == "智己LS8")

        profiles = build_sales_warning_policy_profiles(own, warning["source"]["period"])

        self.assertEqual(profiles[0]["model"], "智己LS8")
        self.assertEqual(profiles[0]["role"], "own")
        self.assertEqual(profiles[0]["salesReference"]["level"], own["level"])
        self.assertEqual([item["role"] for item in profiles[1:4]], ["top3"] * 3)
        self.assertEqual([item["role"] for item in profiles[4:]], ["median"] * len(profiles[4:]))
        self.assertEqual(
            [item["model"] for item in profiles[1:]],
            [item["model"] for item in own["comparisonPeers"]],
        )
        self.assertEqual(
            [item["energyType"] for item in profiles[1:]],
            [item["energyType"] for item in own["comparisonPeers"]],
        )
        self.assertEqual(profiles[0]["energySource"], "懂车帝车型分类")
        self.assertEqual(profiles[0]["energyAsOf"], warning["source"]["period"])
        self.assertTrue(all(item["energySource"] for item in profiles[1:]))
        self.assertTrue(all("/" not in item["energyType"] for item in profiles))
        self.assertNotIn("蔚来ES6", [item["model"] for item in profiles])

    def test_incomplete_vehicle_profile_never_becomes_zero_policy_value(self):
        impact = build_vehicle_policy_impact(
            self.conn,
            model="待核验车型",
            region="上海",
            profile={
                "price": 189900,
                "energyType": "待核验",
                "bodyType": "SUV",
                "purchaseScenario": "置换更新",
            },
            as_of="2026-07-18",
        )

        self.assertEqual(impact["evidenceStatus"], "vehicle_profile_incomplete")
        self.assertIn("energyType", impact["missingProfileFields"])
        self.assertIsNone(impact["maxVerifiedBenefit"])
        self.assertIsNone(impact["maxConditionalBenefit"])
        self.assertIsNone(impact["postPolicyReferencePrice"])
        self.assertIsNone(impact["postPolicyConditionalPrice"])

    def test_multi_powertrain_series_matches_only_policy_scope_covering_every_powertrain(self):
        seed_policy_mvp(self.conn)
        impact = build_vehicle_policy_impact(
            self.conn,
            model="多动力车型",
            region="上海",
            profile={
                "price": 189900,
                "energyType": "增程式/纯电动",
                "bodyType": "SUV",
                "purchaseScenario": "置换更新",
            },
            as_of="2026-07-18",
        )

        self.assertEqual(impact["profile"]["energyTypes"], ["增程式", "纯电动"])
        self.assertEqual(impact["profile"]["energyTypeCodes"], ["EREV", "BEV"])
        self.assertEqual(impact["profile"]["energyResolution"], "normalized")
        self.assertGreater(impact["verifiedPolicyCount"], 0)
        self.assertEqual(impact["evidenceStatus"], "conditional_eligibility")

    def test_energy_contract_normalizes_standard_codes_and_common_separators(self):
        seed_policy_mvp(self.conn)
        cases = (
            ("BEV+EREV", ["纯电动", "增程式"], ["BEV", "EREV"]),
            ("纯电动，增程式", ["纯电动", "增程式"], ["BEV", "EREV"]),
            ("PHEV | BEV", ["插电式混动", "纯电动"], ["PHEV", "BEV"]),
        )
        for raw, labels, codes in cases:
            with self.subTest(raw=raw):
                impact = build_vehicle_policy_impact(
                    self.conn,
                    model="能源别名车型",
                    region="上海",
                    profile={
                        "price": 189900,
                        "energyType": raw,
                        "bodyType": "SUV",
                        "purchaseScenario": "置换更新",
                    },
                    as_of="2026-07-18",
                )
                self.assertEqual(impact["profile"]["energyTypes"], labels)
                self.assertEqual(impact["profile"]["energyTypeCodes"], codes)
                self.assertEqual(impact["profile"]["sourceEnergyText"], raw)
                self.assertEqual(impact["profile"]["energyResolution"], "normalized")

    def test_unknown_energy_token_fails_closed_even_when_mixed_with_known_type(self):
        impact = build_vehicle_policy_impact(
            self.conn,
            model="能源待核验车型",
            region="上海",
            profile={
                "price": 189900,
                "energyType": "BEV/氢能增程",
                "bodyType": "SUV",
                "purchaseScenario": "置换更新",
            },
            as_of="2026-07-18",
        )

        self.assertEqual(impact["evidenceStatus"], "vehicle_profile_incomplete")
        self.assertEqual(impact["profile"]["energyResolution"], "unresolved")
        self.assertEqual(impact["profile"]["unrecognizedEnergyTypes"], ["氢能增程"])
        self.assertIsNone(impact["maxConditionalBenefit"])

    def test_variant_specific_policy_is_not_reported_as_series_wide_zero_or_benefit(self):
        seed_policy_mvp(self.conn)
        self.conn.execute("update policy_records set status='inactive'")
        self.conn.execute(
            """
            update policy_records
               set status='active', policy_type='购置税', region='全国',
                   energy_scope='纯电动', effective_at='2026-01-01',
                   expires_at='2026-12-31'
             where policy_name='2026—2027新能源汽车车辆购置税减免'
            """
        )
        self.conn.execute(
            """
            update policy_records
               set status='active', policy_type='置换更新', region='全国',
                   energy_scope='新能源', effective_at='2026-01-01',
                   expires_at='2026-12-31'
             where policy_name='2026年汽车置换更新补贴'
            """
        )
        impact = build_vehicle_policy_impact(
            self.conn,
            model="双动力车型",
            region="上海",
            profile={
                "price": 189900,
                "energyType": "EREV/BEV",
                "bodyType": "SUV",
                "purchaseScenario": "置换更新",
            },
            as_of="2026-07-18",
        )

        self.assertEqual(impact["evidenceStatus"], "variant_required")
        self.assertEqual(impact["verifiedPolicyCount"], 1)
        self.assertEqual(impact["variantRequiredPolicyCount"], 1)
        self.assertIsNone(impact["maxConditionalBenefit"])
        self.assertIsNone(impact["postPolicyConditionalPrice"])
        self.assertEqual(
            impact["variantRequiredPolicies"][0]["applicableEnergyTypes"],
            ["纯电动"],
        )

    def test_complete_profile_with_no_reviewed_rule_is_a_truthful_zero(self):
        impact = build_vehicle_policy_impact(
            self.conn,
            model="无适用政策车型",
            region="上海",
            profile={
                "price": 189900,
                "energyType": "BEV",
                "bodyType": "SUV",
                "purchaseScenario": "置换更新",
            },
            as_of="2026-07-18",
        )

        self.assertEqual(impact["evidenceStatus"], "no_reviewed_rule")
        self.assertEqual(impact["verifiedPolicyCount"], 0)
        self.assertEqual(impact["maxConditionalBenefit"], 0)
        self.assertEqual(impact["postPolicyConditionalPrice"], 189900)

    def test_nio_peer_uses_baas_base_price_before_policy_calculation(self):
        profiles = build_sales_warning_policy_profiles({
            "model": "奥迪E7X",
            "brand": "上汽奥迪",
            "vehicleStartPriceWan": 26.98,
            "energyType": "纯电动",
            "bodyType": "SUV",
            "comparisonPeers": [{
                "model": "蔚来ES6",
                "manufacturer": "蔚来",
                "startPriceWan": 33.8,
                "priceSource": "dongchedi_dealer_price",
                "role": "top3",
            }],
        }, "2026-06")
        nio = profiles[1]
        self.assertEqual(nio["price"], 268000)
        self.assertEqual(nio["listPrice"], 338000)
        self.assertEqual(nio["baasDiscount"], 70000)
        self.assertIn("BaaS", nio["priceSource"])

        impact = build_vehicle_policy_impact(
            self.conn, model=nio["model"], region="上海", profile={**nio, "purchaseScenario": "置换更新"}, as_of="2026-07-18"
        )
        self.assertEqual(impact["profile"]["priceBasis"], "蔚来BaaS电池租用服务起售价")
        self.assertEqual(impact["profile"]["baasDiscount"], 70000)

    def test_source_url_gate_rejects_non_authoritative_or_private_urls(self):
        self.assertEqual(
            validate_source_url("https://www.mofcom.gov.cn/policy/1", 1),
            "https://www.mofcom.gov.cn/policy/1",
        )
        self.assertEqual(
            validate_source_url("https://www.beijing.gov.cn/policy/1", 2),
            "https://www.beijing.gov.cn/policy/1",
        )
        with self.assertRaises(ValueError):
            validate_source_url("http://127.0.0.1/policy", 1)
        with self.assertRaises(ValueError):
            validate_source_url("https://example.com/policy", 1)

    def test_normalization_defaults_to_pending_and_level_three_cannot_publish(self):
        payload = normalize_policy_json(
            {
                "policyName": "行业观察：置换需求提升",
                "policyLevel": "全国",
                "region": "全国",
                "issuer": "乘联会",
                "policyType": "置换更新",
                "originalUrl": "https://www.cpcaauto.com/news/1",
                "aiSummary": "行业辅助判断",
            },
            {"name": "乘联会", "level": 3, "url": "https://www.cpcaauto.com/news/1"},
        )
        self.assertEqual(payload["reviewStatus"], "pending_verification")
        self.assertEqual(payload["sourceConfidence"], "auxiliary_only")
        self.assertFalse(payload["publishable"])

    def test_document_save_retains_original_text_url_and_hash(self):
        row = save_policy_document(
            self.conn,
            org_id="local",
            edition="china",
            source=OFFICIAL_SOURCE,
            raw_text="2026年汽车以旧换新政策原文。",
            metadata={"policyName": "2026年汽车以旧换新", "publishedAt": "2025-12-30"},
        )
        stored = self.conn.execute("select * from policy_documents where id=?", (row["id"],)).fetchone()
        self.assertEqual(stored["raw_text"], "2026年汽车以旧换新政策原文。")
        self.assertEqual(stored["source_url"], OFFICIAL_SOURCE["url"])
        self.assertEqual(len(stored["raw_sha256"]), 64)
        self.assertEqual(stored["parse_status"], "pending")


class PolicyWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_policy_schema(self.conn)
        seed_policy_sources(self.conn)
        self.raw_text = (
            "2026年，对个人消费者报废符合条件旧车并购买新能源乘用车的，"
            "按新车销售价格的12%给予补贴，补贴金额最高2万元。"
        )
        self.document = save_policy_document(
            self.conn,
            org_id="local",
            edition="china",
            source=OFFICIAL_SOURCE,
            raw_text=self.raw_text,
            metadata={"policyName": "2026年汽车以旧换新补贴实施细则"},
        )

    def tearDown(self):
        self.conn.close()

    def test_model_parse_requires_verbatim_quote_and_never_auto_publishes(self):
        def gateway(_messages):
            return json.dumps(
                {
                    "policyName": "2026年汽车以旧换新补贴实施细则",
                    "policyLevel": "国家",
                    "region": "全国",
                    "issuer": "商务部",
                    "publishedAt": "2025-12-30",
                    "effectiveAt": "2026-01-01",
                    "expiresAt": "2026-12-31",
                    "policyType": "报废更新",
                    "subsidyRate": 0.12,
                    "subsidyCap": 20000,
                    "consumerScope": ["个人消费者", "报废符合条件旧车"],
                    "vehicleScope": ["新能源乘用车"],
                    "energyScope": "新能源",
                    "stackGroup": "2026-national-scrappage",
                    "stackMode": "max",
                    "sourceQuote": "按新车销售价格的12%给予补贴，补贴金额最高2万元",
                    "aiSummary": "符合条件的报废更新新能源购车可按比例获得补贴。",
                    "impactAnalysis": "降低符合条件消费者的购车现金成本。",
                },
                ensure_ascii=False,
            )

        parsed = parse_policy_with_gateway(self.raw_text, OFFICIAL_SOURCE, gateway)
        self.assertEqual(parsed["subsidyRate"], 0.12)
        self.assertEqual(parsed["subsidyCap"], 20000)
        self.assertEqual(parsed["reviewStatus"], "pending_review")
        self.assertFalse(parsed["publishable"])

    def test_model_parse_rejects_claim_not_present_in_original(self):
        def gateway(_messages):
            return json.dumps(
                {
                    "policyName": "虚构政策",
                    "policyLevel": "国家",
                    "region": "全国",
                    "issuer": "商务部",
                    "policyType": "消费券",
                    "sourceQuote": "每辆车额外补贴5万元",
                    "aiSummary": "虚构内容",
                },
                ensure_ascii=False,
            )

        parsed = parse_policy_with_gateway(self.raw_text, OFFICIAL_SOURCE, gateway)
        self.assertEqual(parsed["reviewStatus"], "pending_verification")
        self.assertFalse(parsed["publishable"])
        self.assertTrue(any("逐字引句" in issue for issue in parsed["validationIssues"]))
        record = save_policy_record(self.conn, self.document["id"], parsed)
        self.assertEqual(record["reviewStatus"], "pending_verification")
        self.assertEqual(record["status"], "pending")
        with self.assertRaises(ValueError):
            review_policy(self.conn, record["id"], "approved", "reviewer@mmn")

    def test_review_keeps_version_and_publishes_only_official_policy(self):
        record = save_policy_record(
            self.conn,
            self.document["id"],
            {
                "policyName": "2026年汽车以旧换新补贴实施细则",
                "policyLevel": "国家",
                "region": "全国",
                "issuer": "商务部",
                "publishedAt": "2025-12-30",
                "effectiveAt": "2026-01-01",
                "expiresAt": "2026-12-31",
                "policyType": "报废更新",
                "subsidyRate": 0.12,
                "subsidyCap": 20000,
                "consumerScope": ["个人消费者"],
                "vehicleScope": ["新能源乘用车"],
                "energyScope": "新能源",
                "stackGroup": "2026-national-scrappage",
                "stackMode": "max",
                "originalUrl": OFFICIAL_SOURCE["url"],
                "sourceConfidence": "official_core",
                "sourceQuote": "按新车销售价格的12%给予补贴，补贴金额最高2万元",
                "reviewStatus": "pending_review",
            },
        )
        approved = review_policy(self.conn, record["id"], "approved", "reviewer@mmn", "已核对原文")
        self.assertEqual(approved["reviewStatus"], "approved")
        self.assertEqual(approved["status"], "active")
        self.assertEqual(approved["version"], 2)
        audit = self.conn.execute("select * from policy_reviews where policy_id=?", (record["id"],)).fetchall()
        self.assertEqual(len(audit), 1)
        with self.assertRaises(ValueError):
            review_policy(self.conn, record["id"], "rejected", "other@mmn", org_id="other-tenant")

    def test_eval_uses_five_twenty_point_dimensions_and_preserves_final_version(self):
        analysis_id = "analysis-1"
        self.conn.execute(
            "insert into policy_analysis_results "
            "(id,org_id,edition,model,region,result_json,review_status,final_version,created_at,updated_at) "
            "values (?,?,?,?,?,?,?,?,?,?)",
            (analysis_id, "local", "china", "奥迪E7X", "上海", "{}", "pending", 1, "2026-07-17", "2026-07-17"),
        )
        result = evaluate_policy_analysis(
            self.conn,
            analysis_id,
            {
                "sourceReliability": 20,
                "parsingAccuracy": 18,
                "vehicleMatch": 17,
                "marketingLogic": 16,
                "actionValue": 15,
            },
            reviewer="strategy@mmn",
            note="行动建议需补转化阈值",
        )
        self.assertEqual(result["totalScore"], 86)
        self.assertEqual(result["finalVersion"], 2)
        with self.assertRaises(ValueError):
            evaluate_policy_analysis(
                self.conn,
                analysis_id,
                {field: 20 for field in ("sourceReliability", "parsingAccuracy", "vehicleMatch", "marketingLogic", "actionValue")},
                reviewer="other@mmn",
                org_id="other-tenant",
            )
        with self.assertRaises(ValueError):
            evaluate_policy_analysis(
                self.conn,
                analysis_id,
                {
                    "sourceReliability": 21,
                    "parsingAccuracy": 20,
                    "vehicleMatch": 20,
                    "marketingLogic": 20,
                    "actionValue": 20,
                },
                reviewer="strategy@mmn",
            )

    def test_only_evaluated_analysis_can_feed_opportunity_map_knowledge(self):
        from policy_intelligence import list_policy_knowledge_signals, save_policy_analysis_result

        draft = save_policy_analysis_result(
            self.conn,
            org_id="local",
            edition="china",
            model="奥迪E7X",
            region="上海",
            result={"opportunities": [{"label": "置换窗口", "inference": "已审核规则影响购车门槛", "action": "制作资格解释内容", "factIds": ["p-1"]}]},
        )
        self.assertEqual(list_policy_knowledge_signals(self.conn, org_id="local", edition="china", model="奥迪E7X"), [])
        evaluate_policy_analysis(
            self.conn,
            draft["analysisId"],
            {field: 16 for field in ("sourceReliability", "parsingAccuracy", "vehicleMatch", "marketingLogic", "actionValue")},
            "reviewer@example.com",
        )
        signals = list_policy_knowledge_signals(self.conn, org_id="local", edition="china", model="奥迪E7X")
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["label"], "置换窗口")
        self.assertEqual(signals[0]["evalScore"], 80)
        self.assertEqual(signals[0]["knowledgeStatus"], "evaluated")

    def test_incomplete_three_model_validation_cannot_enter_eval(self):
        from policy_intelligence import save_policy_analysis_result

        draft = save_policy_analysis_result(
            self.conn,
            org_id="local",
            edition="china",
            model="尚界Z7",
            region="广东",
            result={"strategyValidation": {"status": "incomplete", "missingProviders": ["deepseek"]}},
        )
        with self.assertRaisesRegex(ValueError, "三模型验证状态无效"):
            evaluate_policy_analysis(
                self.conn,
                draft["analysisId"],
                {field: 20 for field in EVAL_FIELDS},
                "reviewer@example.com",
            )

    def test_unknown_three_model_validation_status_cannot_enter_eval(self):
        from policy_intelligence import save_policy_analysis_result

        draft = save_policy_analysis_result(
            self.conn,
            org_id="local",
            edition="china",
            model="尚界Z7",
            region="广东",
            result={"strategyValidation": {"status": "unexpected"}},
        )
        with self.assertRaisesRegex(ValueError, "三模型验证状态无效"):
            evaluate_policy_analysis(
                self.conn,
                draft["analysisId"],
                {field: 20 for field in EVAL_FIELDS},
                "reviewer@example.com",
            )

    def test_fetch_task_is_bounded_and_preserves_final_official_url(self):
        def fetcher(url, max_bytes):
            self.assertEqual(url, OFFICIAL_SOURCE["url"])
            self.assertEqual(max_bytes, 800000)
            return {
                "finalUrl": "https://www.mofcom.gov.cn/zfxxgk/final.html",
                "contentType": "text/html; charset=utf-8",
                "body": "<html><body><h1>汽车政策</h1><p>补贴原文</p></body></html>",
                "fetchedAt": "2026-07-17T10:00:00Z",
            }

        result = fetch_policy_source(OFFICIAL_SOURCE, fetcher=fetcher)
        self.assertEqual(result["status"], "fetched")
        self.assertEqual(result["finalUrl"], "https://www.mofcom.gov.cn/zfxxgk/final.html")
        self.assertIn("汽车政策", result["rawText"])
        self.assertNotIn("<h1>", result["rawText"])
        self.assertEqual(len(result["sha256"]), 64)


class PolicyAnalysisTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_policy_schema(self.conn)
        seed_policy_sources(self.conn)

    def tearDown(self):
        self.conn.close()

    def add_policy(self, **overrides):
        raw = overrides.pop(
            "raw_text",
            "对换购新能源乘用车的，按新车销售价格的8%给予补贴，最高1.5万元。",
        )
        source = dict(OFFICIAL_SOURCE)
        document = save_policy_document(
            self.conn,
            org_id="local",
            edition="china",
            source=source,
            raw_text=raw,
            metadata={"policyName": overrides.get("policyName", "汽车置换更新")},
        )
        payload = {
            "policyName": "汽车置换更新",
            "policyLevel": "国家",
            "region": "全国",
            "issuer": "商务部",
            "publishedAt": "2025-12-30",
            "effectiveAt": "2026-01-01",
            "expiresAt": "2026-12-31",
            "policyType": "置换更新",
            "subsidyRate": 0.08,
            "subsidyCap": 15000,
            "consumerScope": ["个人消费者", "转让本人名下旧车"],
            "vehicleScope": ["新能源乘用车"],
            "energyScope": "新能源",
            "stackGroup": "test-stackable-benefit",
            "stackMode": "stackable",
            "originalUrl": source["url"],
            "sourceConfidence": "official_core",
            "sourceQuote": "按新车销售价格的8%给予补贴，最高1.5万元",
            "reviewStatus": "approved",
            "status": "active",
        }
        payload.update(overrides)
        record = save_policy_record(self.conn, document["id"], payload)
        if overrides.get("status") == "expired":
            self.conn.execute("update policy_records set status='expired' where id=?", (record["id"],))
            self.conn.commit()
            return record
        return review_policy(self.conn, record["id"], "approved", "test-reviewer", org_id="local")

    def test_vehicle_impact_uses_active_reviewed_region_and_energy_rules(self):
        self.add_policy()
        self.add_policy(
            policyName="上海新能源促消费",
            policyLevel="市",
            region="上海",
            policyType="地方促销政策",
            subsidyRate=None,
            subsidyAmount=3000,
            subsidyCap=3000,
        )
        self.add_policy(
            policyName="过期消费券",
            region="上海",
            policyType="消费券",
            subsidyAmount=5000,
            subsidyRate=None,
            subsidyCap=5000,
            expiresAt="2025-12-31",
            status="expired",
        )
        result = build_vehicle_policy_impact(
            self.conn,
            model="奥迪E7X",
            region="上海",
            profile={"energyType": "新能源", "price": 280000, "bodyType": "SUV"},
            org_id="local",
            edition="china",
            as_of="2026-07-17",
        )
        self.assertEqual(result["verifiedPolicyCount"], 2)
        self.assertEqual(result["maxVerifiedBenefit"], 0)
        self.assertEqual(result["maxConditionalBenefit"], 18000)
        self.assertEqual(result["evidenceStatus"], "conditional_eligibility")
        self.assertEqual(result["causalBoundary"], "规则影响链，不代表已验证销量因果")
        self.assertTrue(all(item["policyId"] for item in result["policyEffects"]))

    def test_national_nev_rules_apply_to_shanxi_mixed_energy_series(self):
        self.add_policy()
        result = build_vehicle_policy_impact(
            self.conn,
            model="智己LS6",
            region="山西",
            profile={
                "energyType": "增程式/纯电动",
                "energyTypes": ["增程式", "纯电动"],
                "price": 189900,
                "bodyType": "SUV",
                "purchaseScenario": "置换更新",
            },
            org_id="local",
            edition="china",
            as_of="2026-07-31",
        )
        self.assertEqual(result["verifiedPolicyCount"], 1)
        self.assertEqual(result["maxConditionalBenefit"], 15000)
        self.assertEqual(result["postPolicyConditionalPrice"], 174900)
        self.assertEqual(result["evidenceStatus"], "conditional_eligibility")
        self.assertEqual(result["policyEffects"][0]["region"], "全国")

    def test_new_energy_aliases_match_reviewed_nev_policy(self):
        self.add_policy()
        for energy_type in ("纯电", "纯电动", "插混", "插电式混动", "增程", "增程式"):
            with self.subTest(energy_type=energy_type):
                impact = build_vehicle_policy_impact(
                    self.conn,
                    model="测试车型",
                    region="上海",
                    profile={"energyType": energy_type, "price": 219800, "bodyType": "轿车"},
                    org_id="local",
                    edition="china",
                    as_of="2026-07-17",
                )
                self.assertEqual(impact["verifiedPolicyCount"], 1)

    def test_policy_strategy_requires_three_models_and_common_reviewed_evidence(self):
        def output(provider, direction="convert", evidence_ids=None):
            return {
                "policyJudgement": "conditional",
                "strategyDirection": direction,
                "conclusion": "%s区域条件式机会" % provider,
                "targetAudience": "满足置换资格的价格敏感用户",
                "action": "制作资格解释与补贴计算内容",
                "leadingIndicator": "权益内容点击率",
                "conversionIndicator": "有效置换线索率",
                "stopCondition": "连续两周有效线索不增长",
                "uncertainty": "消费者资格尚未逐项确认",
                "evidenceIds": evidence_ids or ["policy-1"],
                "confidence": {"qwen": .78, "deepseek": .82, "kimi": .8}[provider],
            }

        aligned = cross_validate_policy_strategies(
            {provider: output(provider) for provider in ("qwen", "deepseek", "kimi")},
            ["policy-1"],
        )
        self.assertEqual(aligned["status"], "aligned")
        self.assertEqual(aligned["commonEvidenceIds"], ["policy-1"])
        self.assertEqual(aligned["finalStrategy"]["modelAgreement"], "qwen+deepseek+kimi")
        conflicted = cross_validate_policy_strategies(
            {
                "qwen": output("qwen"),
                "deepseek": output("deepseek", direction="educate"),
                "kimi": output("kimi"),
            },
            ["policy-1"],
        )
        self.assertEqual(conflicted["status"], "manual_required")
        self.assertIsNone(conflicted["finalStrategy"])
        self.assertIn("三模型策略方向不一致", conflicted["reasons"])

    def test_supported_policy_regions_cover_mainland_province_level_divisions(self):
        self.assertEqual(len(SUPPORTED_POLICY_REGIONS), 31)
        for region in ("北京", "上海", "重庆", "广东", "内蒙古", "新疆"):
            self.assertIn(region, SUPPORTED_POLICY_REGIONS)

    def test_dashboard_returns_map_trend_vehicle_impact_and_marketing_opportunity(self):
        self.add_policy()
        payload = build_policy_dashboard_payload(
            self.conn,
            model="奥迪E7X",
            region="上海",
            profile={"energyType": "新能源", "price": 280000, "bodyType": "SUV"},
            org_id="local",
            edition="china",
            as_of="2026-07-17",
        )
        self.assertTrue(payload["ok"])
        self.assertIn("map", payload)
        self.assertEqual(len(payload["trend"]), 12)
        self.assertEqual(payload["vehicleImpact"]["model"], "奥迪E7X")
        self.assertEqual(payload["opportunities"][0]["type"], "policy_environment")
        self.assertTrue(payload["opportunities"][0]["factIds"])
        self.assertEqual(payload["opportunities"][0]["reviewStatus"], "pending_human_review")

    def test_mvp_seed_is_source_backed_idempotent_and_dashboard_ready(self):
        first = seed_policy_mvp(self.conn, org_id="local", edition="china")
        second = seed_policy_mvp(self.conn, org_id="local", edition="china")
        self.assertGreaterEqual(first["policyCount"], 4)
        self.assertEqual(second["policyCount"], first["policyCount"])
        rows = self.conn.execute("select * from policy_records").fetchall()
        self.assertTrue(all(row["original_url"].startswith("https://") for row in rows))
        self.assertTrue(all(row["review_status"] == "approved" for row in rows))
        reviewed = self.conn.execute("select count(distinct policy_id) from policy_reviews where decision='approved'").fetchone()[0]
        self.assertEqual(reviewed, len(rows))

    def test_seeded_policy_scenarios_are_exclusive_and_local_implementation_is_not_double_counted(self):
        seed_policy_mvp(self.conn, org_id="local", edition="china")
        replacement = build_vehicle_policy_impact(
            self.conn,
            model="奥迪E7X",
            region="北京",
            profile={
                "energyType": "纯电动",
                "price": 280000,
                "bodyType": "SUV",
                "purchaseScenario": "置换更新",
            },
            org_id="local",
            edition="china",
            as_of="2026-07-17",
        )
        scrappage = build_vehicle_policy_impact(
            self.conn,
            model="奥迪E7X",
            region="北京",
            profile={
                "energyType": "纯电动",
                "price": 280000,
                "bodyType": "SUV",
                "purchaseScenario": "报废更新",
            },
            org_id="local",
            edition="china",
            as_of="2026-07-17",
        )
        direct = build_policy_dashboard_payload(
            self.conn,
            model="奥迪E7X",
            region="北京",
            profile={
                "energyType": "纯电动",
                "price": 280000,
                "bodyType": "SUV",
                "purchaseScenario": "直接购车",
            },
            org_id="local",
            edition="china",
            as_of="2026-07-17",
        )
        replacement_dashboard = build_policy_dashboard_payload(
            self.conn,
            model="奥迪E7X",
            region="北京",
            profile={
                "energyType": "纯电动",
                "price": 280000,
                "bodyType": "SUV",
                "purchaseScenario": "置换更新",
            },
            org_id="local",
            edition="china",
            as_of="2026-07-17",
        )
        scrappage_dashboard = build_policy_dashboard_payload(
            self.conn,
            model="奥迪E7X",
            region="北京",
            profile={
                "energyType": "纯电动",
                "price": 280000,
                "bodyType": "SUV",
                "purchaseScenario": "报废更新",
            },
            org_id="local",
            edition="china",
            as_of="2026-07-17",
        )
        tax_reduction = round(280000 / 1.13 * 0.05)
        self.assertEqual(replacement["maxVerifiedBenefit"], 0)
        self.assertEqual(scrappage["maxVerifiedBenefit"], 0)
        self.assertEqual(replacement["maxConditionalBenefit"], 15000 + tax_reduction)
        self.assertEqual(scrappage["maxConditionalBenefit"], 20000 + tax_reduction)
        self.assertEqual(direct["summary"]["scenarioConditionalBenefit"], tax_reduction)
        self.assertEqual(replacement_dashboard["summary"]["scenarioConditionalBenefit"], 15000 + tax_reduction)
        self.assertEqual(scrappage_dashboard["summary"]["scenarioConditionalBenefit"], 20000 + tax_reduction)
        self.assertEqual(direct["summary"]["purchaseScenario"], "直接购车")
        self.assertGreater(direct["vehicleImpact"]["verifiedPolicyCount"], 0)
        self.assertEqual(sum(item["counted"] for item in replacement["policyEffects"] if item["policyType"] == "置换更新"), 1)
        alias = build_vehicle_policy_impact(
            self.conn,
            model="奥迪E7X",
            region="北京",
            profile={"energyType": "新能源", "price": 280000, "bodyType": "SUV", "scenario": "报废更新", "conditionsConfirmed": True},
            org_id="local",
            edition="china",
            as_of="2026-07-17",
        )
        self.assertEqual(alias["profile"]["purchaseScenario"], "报废更新")
        self.assertFalse(alias["profile"]["conditionsConfirmed"])
        self.assertEqual(alias["maxVerifiedBenefit"], 0)

    def test_seeded_fuel_rules_require_two_liters_or_less_and_apply_rate_caps(self):
        seed_policy_mvp(self.conn, org_id="local", edition="china")
        base_profile = {"energyType": "燃油", "price": 300000, "bodyType": "轿车", "engineDisplacementL": 1.5}
        direct = build_vehicle_policy_impact(
            self.conn, model="荣威i6", region="上海", profile={**base_profile, "purchaseScenario": "直接购车"}, org_id="local", edition="china", as_of="2026-07-18"
        )
        replacement = build_vehicle_policy_impact(
            self.conn, model="荣威i6", region="上海", profile={**base_profile, "purchaseScenario": "置换更新"}, org_id="local", edition="china", as_of="2026-07-18"
        )
        scrappage = build_vehicle_policy_impact(
            self.conn, model="荣威i6", region="上海", profile={**base_profile, "purchaseScenario": "报废更新"}, org_id="local", edition="china", as_of="2026-07-18"
        )
        over_limit = build_vehicle_policy_impact(
            self.conn, model="2.1L燃油车", region="上海", profile={**base_profile, "engineDisplacementL": 2.1, "purchaseScenario": "置换更新"}, org_id="local", edition="china", as_of="2026-07-18"
        )
        self.assertEqual(direct["maxConditionalBenefit"], 0)
        self.assertEqual(replacement["maxConditionalBenefit"], 13000)
        self.assertEqual(scrappage["maxConditionalBenefit"], 15000)
        self.assertEqual(over_limit["maxConditionalBenefit"], 0)
        self.assertEqual(replacement["profile"]["engineDisplacementL"], 1.5)


if __name__ == "__main__":
    unittest.main()
