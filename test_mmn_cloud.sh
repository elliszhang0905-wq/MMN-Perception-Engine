#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${MMN_CLOUD_URL:-http://121.40.60.90:8765}"
OUT_FILE="${MMN_CLOUD_TEST_OUT:-cloud_model_test_result.json}"
SSH_CHECK="${MMN_CLOUD_SSH_CHECK:-true}"
ECS_HOST="${MMN_ECS_HOST:-121.40.60.90}"
ECS_USER="${MMN_ECS_USER:-root}"
ECS_KEY="${MMN_ECS_KEY:-/Users/ellis/.ssh/mmn_ecs_hangzhou_v1}"
MMN_TEST_USERNAME="${MMN_TEST_USERNAME:-Ellis}"
MMN_TEST_PASSWORD="${MMN_TEST_PASSWORD:-Ellis123}"

echo "MMN cloud test target: ${BASE_URL}"

python3 - "$BASE_URL" "$OUT_FILE" "$MMN_TEST_USERNAME" "$MMN_TEST_PASSWORD" <<'PY'
import json
import sys
import time
import urllib.request
import urllib.error

base_url, out_file, test_username, test_password = sys.argv[1:5]
results = []
auth_token = ""

def request_json(method, path, body=None, timeout=180):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    req = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}

def request_text(path, timeout=45):
    with urllib.request.urlopen(base_url.rstrip("/") + path, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")

def record(name, passed, detail="", risk="", data=None, critical=True):
    results.append({
        "name": name,
        "passed": bool(passed),
        "detail": detail,
        "risk": risk,
        "critical": critical,
        "data": data or {},
    })

def run(name, fn, critical=True):
    started = time.time()
    try:
        detail, risk, data = fn()
        record(name, True, detail, risk, data, critical)
    except Exception as exc:
        record(name, False, str(exc), "测试失败，请检查云端服务、网络或模型供应商状态。", critical)
    finally:
        results[-1]["seconds"] = round(time.time() - started, 2)

def check_health():
    data = request_json("GET", "/api/health", timeout=30)
    if not data.get("ok"):
        raise RuntimeError(f"health not ok: {data}")
    return f"健康接口正常，数据库路径：{data.get('db')}", "", data

def check_frontend():
    html = request_text("/", timeout=30)
    ok = "MMN" in html and "app.js" in html
    if not ok:
        raise RuntimeError("首页未检测到 MMN 或 app.js")
    return "首页 HTML 可访问，前端资源入口存在。", "", {"htmlLength": len(html)}

def check_cloud_login():
    global auth_token
    config = request_json("GET", "/api/auth/config", timeout=30)
    if not config.get("loginRequired"):
        return "云端未开启登录门禁，按本地免登录模式测试。", "如目标是服务器演示环境，应确认 MMN_CLOUD_LOGIN_REQUIRED=true。", config
    data = request_json("POST", "/api/login", {"username": test_username, "password": test_password}, timeout=30)
    token = data.get("session", {}).get("token")
    if not token:
        raise RuntimeError("登录成功但未返回 token")
    auth_token = token
    return f"云端登录成功：{data.get('session', {}).get('username')} / {data.get('session', {}).get('role')}", "", {
        "role": data.get("session", {}).get("role"),
        "permissions": data.get("session", {}).get("permissions", []),
    }

def check_ai_status():
    data = request_json("GET", "/api/ai/status", timeout=30)
    qwen = data.get("qwen", {}).get("configured")
    deepseek = data.get("deepseek", {}).get("configured")
    if not qwen or not deepseek:
        raise RuntimeError(f"模型配置不完整：qwen={qwen}, deepseek={deepseek}")
    return (
        f"Qwen={data.get('qwen', {}).get('model')}，DeepSeek={data.get('deepseek', {}).get('model')}，规则引擎={data.get('rules', {}).get('configured')}",
        "只验证 Key 已进入运行环境，不输出 Key 明文。",
        data,
    )

def check_rag_seed():
    data = request_json("POST", "/api/import-rag-seed", {}, timeout=60)
    items = data.get("dataset", {}).get("items", [])
    if not data.get("ok") or len(items) < 1:
        raise RuntimeError(f"RAG 种子包未返回有效条目：{data}")
    return f"RAG 种子包可解析，召回/导入候选 {len(items)} 条。", "", {"count": len(items)}

def check_strategy_fast():
    data = request_json("POST", "/api/ai/rag-strategy", {
        "question": "智己LS8小红书自然声量低，下一步怎么打？",
        "mode": "fast",
        "project": {
            "brand": "智己",
            "model": "智己LS8",
            "competitor": "理想L8 / 问界M7",
            "stage": "上市期"
        },
        "references": [{
            "title": "智己LS8正反向竞争格局",
            "type": "垂媒竞争",
            "body": "懂车帝正向排名显示用户常把智己LS8与理想L8、问界M7等家庭SUV比较，核心疑虑集中在空间、价格权益和智驾可信度。",
            "source": "MMN云端测试知识库",
            "keywords": ["智己LS8", "理想L8", "正反向排名", "家庭SUV"]
        }]
    }, timeout=180)
    text = data.get("text") or ""
    if not data.get("ok") or len(text) < 120:
        raise RuntimeError(f"策略结果过短或失败：{data}")
    if data.get("model") == "local-rag":
        raise RuntimeError("策略接口回落到本地规则，未实际使用外部模型。")
    return f"策略生成正常，使用模型：{data.get('model')}，输出 {len(text)} 字。", "", {
        "model": data.get("model"),
        "modelLabel": data.get("modelLabel"),
        "textPreview": text[:160],
        "errors": data.get("errors", {}),
    }

def check_strategy_deep():
    data = request_json("POST", "/api/ai/rag-strategy", {
        "question": "请判断智己LS8相对理想L8的认知空位，并给出下一步动作。",
        "mode": "deep",
        "project": {
            "brand": "智己",
            "model": "智己LS8",
            "competitor": "理想L8",
            "stage": "上市期"
        },
        "references": [{
            "title": "家庭SUV竞品心智",
            "type": "RAG测试资料",
            "body": "用户把智己LS8与理想L8比较，关注家庭场景、智驾可信度、空间舒适和价格权益。",
            "source": "MMN云端测试知识库",
            "keywords": ["智己LS8", "理想L8", "认知空位", "家庭SUV"]
        }]
    }, timeout=220)
    text = data.get("text") or ""
    if not data.get("ok") or len(text) < 120:
        raise RuntimeError(f"深度策略结果过短或失败：{data}")
    if data.get("model") == "local-rag":
        raise RuntimeError("深度策略接口回落到本地规则，未实际使用外部模型。")
    return f"深度策略生成正常，使用模型：{data.get('model')}，输出 {len(text)} 字。", "", {
        "model": data.get("model"),
        "modelLabel": data.get("modelLabel"),
        "textPreview": text[:160],
        "errors": data.get("errors", {}),
    }

def check_fusion_models():
    data = request_json("POST", "/api/ai/fusion-strategy", {
        "context": {
            "brand": "智己",
            "model": "智己LS8",
            "competitor": "理想L8",
            "label": "空间舒适",
            "diagnosis": "抢占空位",
            "platform": "小红书",
            "question": "如何把家庭SUV空间舒适打成小红书自然声量？"
        }
    }, timeout=240)
    parts = data.get("parts") or {}
    if not data.get("ok") or not parts.get("qwen") or not parts.get("deepseek"):
        raise RuntimeError(f"双模型融合未同时返回 Qwen 与 DeepSeek：{data.get('errors')}")
    return "双模型路径正常，Qwen 与 DeepSeek 均返回内容。", "", {
        "qwenLength": len(parts.get("qwen") or ""),
        "deepseekLength": len(parts.get("deepseek") or ""),
        "errors": data.get("errors", {}),
    }

def check_identity_write():
    data = request_json("POST", "/api/ai/model-identities", {
        "edition": "china",
        "models": ["阿维塔06", "沃尔沃EX90", "Zeekr 009", "极氪009"]
    }, timeout=180)
    items = data.get("items") or []
    if not data.get("ok") or len(items) < 4:
        raise RuntimeError(f"车型身份识别失败：{data}")
    return f"车型身份识别正常，写入/返回 {len(items)} 条，使用模型：{data.get('model')}。", "", {
        "model": data.get("model"),
        "items": items,
        "errors": data.get("errors", {}),
    }

def check_judgment_write():
    data = request_json("POST", "/api/ai/model-judgment", {
        "edition": "china",
        "text": "智己LS8最大问题不是配置，而是家庭用户还没有看到足够真实的第三方空间验证。",
        "project": {
            "brand": "智己",
            "model": "智己LS8",
            "competitor": "理想L8"
        }
    }, timeout=180)
    if not data.get("ok") or not data.get("item"):
        raise RuntimeError(f"车型判断未写入：{data}")
    return f"车型判断写入正常，使用模型：{data.get('model')}。", "", {
        "model": data.get("model"),
        "itemId": data.get("item", {}).get("id"),
        "knowledgeItem": bool(data.get("knowledgeItem")),
        "errors": data.get("errors", {}),
    }

run("health", check_health)
run("frontend", check_frontend)
run("cloud_login", check_cloud_login)
run("ai_status", check_ai_status)
run("rag_seed_parse", check_rag_seed)
run("strategy_fast_generation", check_strategy_fast)
run("strategy_deep_generation", check_strategy_deep)
run("fusion_qwen_deepseek", check_fusion_models, critical=False)
run("model_identity_write", check_identity_write)
run("model_judgment_write", check_judgment_write)

summary = {
    "target": base_url,
    "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "passed": all(item["passed"] or not item["critical"] for item in results),
    "results": results,
}

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

for item in results:
    icon = "PASS" if item["passed"] else "FAIL"
    print(f"[{icon}] {item['name']} - {item['detail']}")
    if item.get("risk"):
        print(f"       risk: {item['risk']}")

print(f"测试结果已写入：{out_file}")
if not summary["passed"]:
    sys.exit(1)
PY

if [[ "$SSH_CHECK" == "true" && -f "$ECS_KEY" ]]; then
  echo "MMN cloud database count check via SSH..."
  ssh -i "$ECS_KEY" -o StrictHostKeyChecking=no "${ECS_USER}@${ECS_HOST}" "docker exec -i mmn-app python -" <<'PY'
import sqlite3
conn = sqlite3.connect('/app/data/commercial_demo.db')
for table in [
    'workspace_contexts',
    'project_snapshots',
    'vehicle_assets',
    'vertical_rank_assets',
    'vertical_ai_learnings',
    'model_identity_assets',
    'model_judgment_assets',
    'founder_speech_archives',
    'learning_cases',
]:
    try:
        print(f"{table}: {conn.execute(f'select count(*) from {table}').fetchone()[0]}")
    except Exception as exc:
        print(f"{table}: ERR {exc}")
PY
fi

echo "MMN cloud test completed."
