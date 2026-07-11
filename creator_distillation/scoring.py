import math
from datetime import datetime, timezone


def _num(value):
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _rate(value, views):
    return min(1.0, _num(value) / max(1.0, _num(views)))


def score_assets(assets, followers=0, now=None):
    """Explainable, within-account normalized performance score."""
    now = now or datetime.now(timezone.utc)
    raw = []
    for item in assets:
        views = _num(item.get("views"))
        followers_n = max(1.0, _num(followers))
        published = item.get("published_at")
        try:
            published_dt = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
            age_days = max(0, (now - published_dt).days)
        except (TypeError, ValueError):
            age_days = 180
        velocity = math.log1p(views / followers_n)
        engagement = (_rate(item.get("likes"), views) * .32 + _rate(item.get("comments"), views) * .22 +
                      _rate(item.get("collects"), views) * .25 + _rate(item.get("shares"), views) * .21)
        recency = math.exp(-age_days / 240)
        raw.append(velocity * .38 + engagement * 8 * .42 + recency * .20)
    ranked = sorted(raw)
    results = []
    for index, item in enumerate(assets):
        percentile = (sum(1 for value in ranked if value <= raw[index]) / max(1, len(ranked)))
        tags = list(item.get("interference_tags") or [])
        noise = sum({"commercial": .13, "paid_traffic": .18, "trend": .10, "anomaly": .24}.get(tag, 0) for tag in tags)
        final = max(0, min(100, (raw[index] * .65 + percentile * .35 - noise) * 100))
        if noise >= .18:
            final *= .45
        reasons = [f"账号内表现位于前 {max(1, round((1-percentile)*100))}%"]
        if _rate(item.get("comments"), item.get("views")) >= .01: reasons.append("评论率突出")
        if _rate(item.get("collects"), item.get("views")) >= .01: reasons.append("收藏率突出")
        if tags: reasons.append("已降权: " + "、".join(tags))
        stability = "noise" if noise >= .18 else "stable" if percentile >= .5 else "supporting"
        results.append({**item, "performance_score": round(final, 2), "relative_percentile": round(percentile, 4),
                        "selection_reasons": reasons, "sample_role": stability})
    return sorted(results, key=lambda x: x["performance_score"], reverse=True)


def select_diverse_samples(assets, count=50):
    chosen, per_topic = [], {}
    for item in assets:
        topic = str(item.get("primary_tag") or "未分类")
        if per_topic.get(topic, 0) >= max(3, math.ceil(count * .35)):
            continue
        chosen.append(item); per_topic[topic] = per_topic.get(topic, 0) + 1
        if len(chosen) >= count: break
    if len(chosen) < count:
        ids = {x.get("source_id") for x in chosen}
        chosen.extend(x for x in assets if x.get("source_id") not in ids and len(chosen) < count)
    return chosen
