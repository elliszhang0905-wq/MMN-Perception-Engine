#!/usr/bin/env python3
"""Explicit opt-in external GEO worker; SIGTERM stops issuing new calls."""
import argparse
from pathlib import Path
import signal
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime_config import initialize_runtime_config
from geo.config import load_settings
from geo.repository import GeoRepository
from geo.worker import GeoWorker


def main():
    parser = argparse.ArgumentParser(description="MMN GEO 持久任务worker")
    parser.add_argument("--db", required=True, help="与GEO服务使用的数据库一致；独立部署时对应MMN_GEO_DB_PATH")
    parser.add_argument("--once", action="store_true", help="最多处理一个已排队观测")
    args = parser.parse_args()
    initialize_runtime_config(root=Path(__file__).resolve().parent.parent)
    settings = load_settings()
    if not settings["enabled"] or not settings["real_sampling_enabled"] or settings["worker_mode"] != "external":
        print("GEO worker未启用：检查模块、真实采样与external配置；未创建数据库或发起调用。")
        return 2
    if settings["configuration_errors"] or not settings["api_key"] or not settings["model"]:
        print("GEO worker配置不完整；请在后端安全配置凭证、模型和配额。")
        return 2
    worker = GeoWorker(GeoRepository(args.db), settings)
    signal.signal(signal.SIGTERM, lambda *_: worker.stop.set())
    signal.signal(signal.SIGINT, lambda *_: worker.stop.set())
    if args.once:
        print("已处理一个观测。" if worker.tick() else "当前无可执行观测。")
        return 0
    threads = [threading.Thread(target=worker.run, daemon=True) for _ in range(settings["max_concurrency"])]
    for thread in threads: thread.start()
    while not worker.stop.wait(1): pass
    for thread in threads: thread.join(timeout=125)
    print("GEO worker已安全停止；已发生或未知费用保留。")
    return 0


if __name__ == "__main__": sys.exit(main())
