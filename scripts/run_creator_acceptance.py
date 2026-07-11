#!/usr/bin/env python3
"""Run only with consented public test-account fixtures and a real TikHub key."""
import argparse, json, os, statistics, time
from pathlib import Path
from creator_distillation.service import CreatorDistillationService

def main():
    ap=argparse.ArgumentParser();ap.add_argument("fixture",type=Path);ap.add_argument("--out",type=Path,default=Path("output/creator-acceptance.json"));args=ap.parse_args()
    if not os.getenv("TIKHUB_API_KEY"): raise SystemExit("TIKHUB_API_KEY 未配置；禁止把模拟验收标记为真实验收")
    accounts=json.loads(args.fixture.read_text())
    counts={p:sum(1 for x in accounts if x.get("platform")==p) for p in ("douyin","xiaohongshu")}
    if min(counts.values())<10: raise SystemExit("验收集要求抖音和小红书各至少 10 个脱敏公开账号")
    service=CreatorDistillationService();results=[]
    for item in accounts:
        started=time.monotonic()
        try:
            preflight=service.preflight(item["url"]);results.append({"accountRef":item["ref"],"platform":item["platform"],"ok":True,"preflight":preflight,"elapsedSeconds":round(time.monotonic()-started,3),"cost":None,"manualIntervention":[]})
        except Exception as exc:
            results.append({"accountRef":item["ref"],"platform":item["platform"],"ok":False,"reason":str(exc),"elapsedSeconds":round(time.monotonic()-started,3),"cost":None,"manualIntervention":["检查接口版本或补充公开素材"]})
    report={"status":"production-data-validation-started","realKey":True,"counts":counts,"successRate":sum(x["ok"] for x in results)/len(results),"averageSeconds":statistics.mean(x["elapsedSeconds"] for x in results),"results":results,"requiredE2EPerPlatform":3,"note":"只有补齐采集、处理、DNA、检索及故障注入结果后才可标记可部署"}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(args.out)
if __name__=="__main__":main()
