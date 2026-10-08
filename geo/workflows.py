"""Evidence preserving, tenant scoped manual GEO workflows; no network or execution."""
import base64
import binascii
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import re
from urllib.parse import urlsplit

from .analysis import analyze_answer
from .metrics import compute_metrics
from .store import GeoError, decoded, dumps, fingerprint, integer, stamp, text_value, uid


_IMPORT_FIELDS = {'question_version_id', 'question_text', 'answer', 'sampled_at', 'new_session',
    'personalization', 'visible_search', 'platform_trace_id', 'paired_observation_id',
    'screenshot_base64', 'screenshot_mime', 'batch_id', 'repeat_index', 'condition_id', 'actual_model'}
_ACTION_TEXT = {'title': 300, 'diagnosis': 6000, 'product_point': 4000, 'fact_to_add': 4000,
    'content_structure': 6000, 'carrier': 500, 'owner': 160, 'execution_evidence': 6000}


def _iso(value, label, required=False):
    if value in (None, ''):
        if required:
            raise GeoError(f'{label}必须为带时区ISO日期时间')
        return None
    value = text_value(value, label, 64, True)
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value):
        raise GeoError(f'{label}必须为带时区ISO日期时间')
    try:
        when = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if when.utcoffset() is None:
            raise ValueError()
    except (ValueError, TypeError):
        raise GeoError(f'{label}日期时间无效') from None
    return when.astimezone(timezone.utc).isoformat()


def _when(value):
    try:
        normalized = _iso(value, '时间')
        return datetime.fromisoformat(normalized) if normalized else None
    except GeoError:
        return None


def _valid(obs):
    return (obs.get('status') == 'completed' and bool(obs.get('answer', '').strip())
        and (obs.get('analysis') or {}).get('valid_answer') is True)


def _screenshot(payload):
    encoded = payload.get('screenshot_base64')
    mime = payload.get('screenshot_mime')
    if encoded is None and mime is None:
        return None
    if not isinstance(encoded, str) or not encoded or len(encoded) > 4 * ((2 * 1024 * 1024 + 2) // 3):
        raise GeoError('截图须为不超过2MB的PNG/JPEG Base64')
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise GeoError('截图Base64格式错误') from None
    magic = {'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff'}
    if not isinstance(mime, str) or mime not in magic or len(content) > 2 * 1024 * 1024 or not content.startswith(magic[mime]):
        raise GeoError('截图类型或内容不符合PNG/JPEG要求')
    return mime, content, hashlib.sha256(content).hexdigest()


def _links(answer):
    urls = re.findall(r'https?://[^\s<>"\x00-\x20\u3000]+', answer)
    result = []
    for url in urls:
        url = url.rstrip('.,;!?。，；！？）)]}')
        try:
            parsed = urlsplit(url)
            if parsed.hostname and not parsed.username and len(url) <= 2048:
                result.append({'url': url, 'normalized_url': url, 'source_type': 'text_link',
                    'fetch_status': 'not_fetched', 'status': 'not_fetched'})
        except ValueError:
            pass
    return list({x['url']: x for x in result}.values())


class WorkflowMixin:
    def _manual_condition(self, conn, org, project, visible, actor):
        value = {'surface': 'doubao_app_manual', 'mode': {'on': 'search_enabled', 'off': 'non_search', 'unknown': 'unknown'}[visible],
            'api_mode': 'manual', 'temperature': None, 'seed': None, 'capabilities': None,
            'provider_config_hash': None, 'model_config_version': None, 'model': '',
            'system_prompt_version': 'neutral-v1', 'system_prompt': '', 'max_output_tokens': 2048,
            'timeout_seconds': 60}
        key = fingerprint(value)
        existing = conn.execute('SELECT * FROM geo_condition WHERE org_id=? AND project_id=? AND condition_hash=?', (org, project, key)).fetchone()
        if existing:
            return decoded(existing)
        ident = uid('condition')
        self._insert(conn, 'geo_condition', {'id': ident, 'org_id': org, 'project_id': project,
            'condition_hash': key, 'payload_json': dumps(value), 'created_at': stamp()})
        self._audit(conn, org, project, 'condition_created', ident, actor, {'condition_hash': key})
        return self._get(conn, 'geo_condition', org, ident, project)

    def import_app(self, org, project_id, payload, actor='local'):
        if not isinstance(payload, dict) or set(payload) - _IMPORT_FIELDS:
            raise GeoError('App导入字段不合法；不支持URL截图或本地路径')
        qid = text_value(payload.get('question_version_id'), '问题版本', 160, True)
        actor = text_value(actor, '审计身份', 160, True)
        batch_id = text_value(payload.get('batch_id'), '批次标识', 160)
        condition_id = text_value(payload.get('condition_id'), '条件标识', 160)
        requested_repeat = integer(payload.get('repeat_index', 1), '重复编号', 1, 10)
        if not batch_id and (requested_repeat != 1 or condition_id):
            raise GeoError('单样本导入不能指定额外重复或其他条件')
        question_text = text_value(payload.get('question_text'), '问题全文', 2000)
        text_value(payload.get('answer'), '答案全文', 200000)
        answer = payload.get('answer') or ''
        sampled = _iso(payload.get('sampled_at'), '采样时间')
        metadata = {}
        for field in ('new_session', 'personalization', 'visible_search'):
            value = payload.get(field, 'unknown')
            if value is None:
                value = 'unknown'
            if field == 'new_session':
                if not isinstance(value, bool) and value != 'unknown':
                    raise GeoError('新会话状态须为布尔值或unknown')
            elif not isinstance(value, str) or value not in {'on', 'off', 'unknown'}:
                raise GeoError(f'{field}状态错误')
            metadata[field] = value
        metadata['platform_trace_id'] = text_value(payload.get('platform_trace_id'), '平台traceID', 200) or None
        metadata['paired_observation_id'] = text_value(payload.get('paired_observation_id'), '配对观测', 160) or None
        actual_model = text_value(payload.get('actual_model'), '实际模型标识', 200) or None
        shot = _screenshot(payload)
        with self.connect(True) as conn:
            self._get(conn, 'geo_project', org, project_id)
            question = self._get(conn, 'geo_question_version', org, qid, project_id)
            if metadata['paired_observation_id']:
                pair = self._get(conn, 'geo_observation', org, metadata['paired_observation_id'], project_id)
                if pair['channel'] == 'doubao_app_manual' or pair['question_version_id'] != qid:
                    raise GeoError('配对须为当前项目同问题版本的API观测')
            if batch_id:
                batch = self._get(conn, 'geo_batch', org, batch_id, project_id)
                conditions = [x for x in batch['manifest']['conditions'] if x['surface'] == 'doubao_app_manual' and x['api_mode'] == 'manual']
                if not batch['manifest'].get('manual') or qid not in {x['id'] for x in batch['manifest']['questions']}:
                    raise GeoError('批次不包含该问题或不是人工采样批次')
                if condition_id:
                    conditions = [x for x in conditions if x['id'] == condition_id]
                if len(conditions) != 1:
                    raise GeoError('人工批次须明确唯一采样条件')
                condition = conditions[0]
                repeat = integer(requested_repeat, '重复编号', 1, batch['manifest']['repeats'])
            else:
                condition = self._manual_condition(conn, org, project_id, metadata['visible_search'], actor)
                repeat = 1
                batch_id = self._create_batch(conn, org, project_id, {'question_version_ids': [qid],
                    'condition_ids': [condition['id']], 'repeats': 1, 'idempotency_key': uid('import')}, {}, actor)
                batch = self._get(conn, 'geo_batch', org, batch_id, project_id)
            if metadata['visible_search'] != 'unknown' and {'on': 'search_enabled', 'off': 'non_search'}[metadata['visible_search']] != condition['mode']:
                raise GeoError('可见搜索设置与冻结采样条件不同，请新建独立条件批次')
            if batch['status'] == 'cancelled':
                raise GeoError('已取消批次不能导入')
            obs = decoded(conn.execute('SELECT * FROM geo_observation WHERE org_id=? AND project_id=? AND batch_id=? AND question_version_id=? AND condition_id=? AND repeat_index=?',
                (org, project_id, batch['id'], qid, condition['id'], repeat)).fetchone())
            if obs['raw_hash'] is not None or obs['status'] != 'draft':
                raise GeoError('该采样位置已有证据，不能覆盖', 'evidence_conflict', 409)
            question = next(x for x in batch['manifest']['questions'] if x['id'] == qid)
            exact = bool(question_text) and question_text == question['text']
            analysis = analyze_answer(answer, batch['manifest']['entities'], batch['manifest']['facts'], observed_at=sampled, question=question)
            if not exact:
                analysis.update(valid_answer=False, question_verified=False, exclusion_reason='question_not_verified')
            else:
                analysis['question_verified'] = True
            status = 'empty' if not answer.strip() else ('completed' if analysis['valid_answer'] else ('refused' if analysis.get('refusal') else 'unanalysable'))
            metadata.update(question_verified=exact, sampled_at=sampled, visible_search_is_actual_event=False)
            raw = {'evidence_origin': 'manual_import', 'question_text': question_text, 'answer': answer,
                'sample_metadata': metadata, 'actual_model': actual_model}
            info = {'actual_model': actual_model, 'request_id': metadata['platform_trace_id'],
                'search_requested': None, 'search_observed': None, 'sample_time_unknown': sampled is None}
            conn.execute('UPDATE geo_observation SET status=?,answer=?,raw_json=?,raw_hash=?,analysis_json=?,sample_metadata_json=?,payload_json=?,sampled_at=?,evidence_origin=? WHERE org_id=? AND id=? AND raw_hash IS NULL',
                (status, answer, dumps(raw), fingerprint(raw), dumps(analysis), dumps(metadata), dumps(info), sampled, 'manual_import', org, obs['id']))
            for citation in _links(answer):
                self._insert(conn, 'geo_citation', {'id': uid('citation'), 'org_id': org, 'project_id': project_id,
                    'observation_id': obs['id'], 'payload_json': dumps(citation), 'created_at': stamp()})
            if shot:
                self._insert(conn, 'geo_screenshot', {'id': uid('screenshot'), 'org_id': org, 'project_id': project_id,
                    'observation_id': obs['id'], 'mime': shot[0], 'content': shot[1], 'sha256': shot[2], 'created_at': stamp()})
            self._audit(conn, org, project_id, 'app_evidence_imported', obs['id'], actor,
                {'raw_hash': fingerprint(raw), 'question_verified': exact, 'status': status})
            self._finalize(conn, org, batch['id'])
            ident = obs['id']
        return self.get_observation(org, ident)

    def apply_reviews(self, obs):
        result = deepcopy(obs)
        automatic = deepcopy(obs.get('automatic_analysis', obs.get('analysis')))
        effective = deepcopy(automatic or {})
        for review in obs.get('reviews') or []:
            kind = review.get('kind')
            if kind == 'entity':
                row = next((x for x in effective.get('entities', []) if x['entity_key'] == review['entity_key']), None)
            elif kind == 'fact':
                rows = effective.get('fact_checks', [])
                index = review.get('fact_index', -1)
                row = rows[index] if isinstance(index, int) and 0 <= index < len(rows) else None
            else:
                row = None
            if row is not None:
                row.update(review.get('changes', {}))
                row['reviewed'] = True
        result.update(automatic_analysis=automatic, analysis=effective if automatic is not None else None,
            reviewed=bool(obs.get('reviews')))
        return result

    def add_review(self, org, observation_id, payload, actor='local'):
        actor = text_value(actor, '复核身份', 160, True)
        if not isinstance(payload, dict):
            raise GeoError('复核内容须为对象')
        reason = text_value(payload.get('reason'), '复核理由', 2000, True)
        kind, changes = payload.get('kind'), payload.get('changes')
        allowed = {'entity': {'mentioned', 'recommended', 'rank', 'needs_review', 'evidence'},
            'fact': {'verdict', 'needs_review', 'baseline_id', 'evidence'}}
        if not isinstance(kind, str) or kind not in allowed or not isinstance(changes, dict) or not changes or set(changes) - allowed[kind]:
            raise GeoError('复核类型或修改字段错误')
        changes = deepcopy(changes)
        for field in ('mentioned', 'recommended', 'needs_review'):
            if field in changes and not isinstance(changes[field], bool):
                raise GeoError(f'{field}必须为布尔值')
        if 'evidence' in changes:
            changes['evidence'] = text_value(changes['evidence'], '证据片段', 6000, True)
        with self.connect(True) as conn:
            obs = self._observation_detail(conn, self._get(conn, 'geo_observation', org, observation_id))
            effective = self.apply_reviews(obs)['analysis'] or {}
            value = {'kind': kind, 'changes': changes}
            if kind == 'entity':
                key = text_value(payload.get('entity_key'), '实体标识', 120, True)
                row = next((x for x in effective.get('entities', []) if x['entity_key'] == key), None)
                if row is None:
                    raise GeoError('复核实体不属于冻结项目实体')
                value['entity_key'] = key
                new = {**row, **changes}
                if new.get('recommended') is True and new.get('mentioned') is not True:
                    raise GeoError('推荐实体必须同时被提及')
                if new.get('rank') is not None:
                    if not isinstance(new['rank'], int) or isinstance(new['rank'], bool):
                        raise GeoError('推荐排序必须为整数')
                    new['rank'] = integer(new['rank'], '推荐排序', 1, 1000)
                    if new.get('recommended') is not True:
                        if 'rank' in changes:
                            raise GeoError('排序只能用于明确推荐')
                        changes['rank'] = new['rank'] = None
                if any(changes.get(x) is True for x in ('mentioned', 'recommended')):
                    evidence = changes.get('evidence') or row.get('evidence')
                    if not evidence or evidence not in obs['answer']:
                        raise GeoError('人工确认须有原答案中的实际证据片段')
            else:
                rows = effective.get('fact_checks', [])
                index = integer(payload.get('fact_index'), '事实编号', 0, max(0, len(rows)-1))
                if index >= len(rows):
                    raise GeoError('事实不存在')
                row = rows[index]
                value['fact_index'] = index
                new = {**row, **changes}
                if not isinstance(new.get('verdict'), str) or new['verdict'] not in {'supported', 'contradicted', 'outdated', 'unverified', 'subjective', 'not_applicable', 'conflicting_sources'}:
                    raise GeoError('事实判断错误')
                if 'baseline_id' in changes:
                    changes['baseline_id'] = text_value(changes['baseline_id'], '事实基准', 160, True)
                    self._get(conn, 'geo_fact_baseline', org, changes['baseline_id'], obs['project_id'])
                if new.get('verdict') in {'supported', 'contradicted', 'outdated'}:
                    baseline_id = changes.get('baseline_id') or row.get('baseline_id')
                    if not isinstance(baseline_id, str):
                        raise GeoError('事实核验需要已审核基准')
                    baseline = self._get(conn, 'geo_fact_baseline', org, baseline_id, obs['project_id'])
                    required = ('logical_id', 'version', 'year', 'trim', 'market', 'field', 'unit', 'source_url', 'source_excerpt', 'reviewer', 'effective_from')
                    if (baseline.get('state') != 'approved' or any(baseline.get(x) in (None, '') for x in required)
                        or not isinstance(baseline.get('conditions'), dict) or not baseline['conditions']
                        or not str(baseline['source_url']).startswith('https://') or 'value' not in baseline
                        or baseline.get('entity_key') != row.get('entity_key') or baseline.get('field') != row.get('field')):
                        raise GeoError('事实基准缺少审核、来源或适用条件')
                    evidence = changes.get('evidence') or row.get('evidence')
                    if not evidence or evidence not in obs['answer']:
                        raise GeoError('核验结论需要原答案证据；无证据只能未核验')
                    changes['baseline_id'] = new['baseline_id'] = baseline_id
            value.update(old=deepcopy(row), new={**row, **changes})
            ident = uid('review')
            self._insert(conn, 'geo_review', {'id': ident, 'org_id': org, 'project_id': obs['project_id'],
                'observation_id': observation_id, 'payload_json': dumps(value), 'actor': actor,
                'reason': reason, 'created_at': stamp()})
            self._audit(conn, org, obs['project_id'], 'observation_reviewed', ident, actor,
                {'observation_id': observation_id, 'kind': kind, 'old': value['old'], 'new': value['new'], 'reason': reason})
            return self._get(conn, 'geo_review', org, ident)

    def save_action(self, org, project_id, payload, actor='local', action_id=None):
        actor = text_value(actor, '动作身份', 160, True)
        allowed = set(_ACTION_TEXT) | {'observation_ids', 'entity_key', 'entity_keys', 'status', 'executed_at'}
        if not isinstance(payload, dict) or set(payload) - allowed:
            raise GeoError('动作字段错误')
        with self.connect(True) as conn:
            project = self._get(conn, 'geo_project', org, project_id)
            old = self._get(conn, 'geo_action', org, action_id, project_id) if action_id else None
            value = {k: old.get(k) for k in allowed | {'approved_by', 'approved_at'} if old and k in old}
            value.update(payload)
            for field, limit in _ACTION_TEXT.items():
                value[field] = text_value(value.get(field), field, limit, field == 'title')
            entries = value.get('observation_ids', [])
            if not isinstance(entries, list) or len(entries) > 100 or any(not isinstance(x, str) for x in entries):
                raise GeoError('关联观测格式错误')
            value['observation_ids'] = list(dict.fromkeys(entries))
            for ident in entries:
                self._get(conn, 'geo_observation', org, ident, project_id)
            keys = value.get('entity_keys', [])
            if not isinstance(keys, list) or len(keys) > 10:
                raise GeoError('关联实体格式错误')
            if value.get('entity_key'):
                keys = [*keys, value['entity_key']]
            if any(not isinstance(x, str) or x not in {e['key'] for e in project['entities']} for x in keys):
                raise GeoError('关联实体不属于项目')
            value['entity_keys'] = list(dict.fromkeys(keys))
            state = value.get('status', 'draft')
            if not isinstance(state, str) or state not in {'draft', 'approved', 'executed'} or (old is None and state != 'draft'):
                raise GeoError('初始动作须为draft，状态必须为draft/approved/executed')
            prior = old.get('status') if old else None
            if prior == 'executed' and state != 'executed':
                raise GeoError('已执行动作不能退回未执行状态')
            if state == 'approved' and prior != 'approved':
                value.update(approved_by=actor, approved_at=stamp())
            if state == 'draft':
                value.pop('approved_by', None)
                value.pop('approved_at', None)
            value['status'] = state
            value['executed_at'] = _iso(value.get('executed_at'), '执行时间', state == 'executed')
            if state == 'executed':
                if prior not in {'approved', 'executed'} or not value.get('approved_by') or not value['execution_evidence']:
                    raise GeoError('执行动作需要先批准并提供真实执行证据与时间')
                if prior == 'executed' and any(value.get(k) != old.get(k) for k in ('executed_at', 'execution_evidence')):
                    raise GeoError('已执行时间和执行证据不能被覆盖；请另建动作')
            ident, now = action_id or uid('action'), stamp()
            if old:
                conn.execute('UPDATE geo_action SET payload_json=?,updated_at=? WHERE org_id=? AND project_id=? AND id=?', (dumps(value), now, org, project_id, ident))
            else:
                self._insert(conn, 'geo_action', {'id': ident, 'org_id': org, 'project_id': project_id,
                    'payload_json': dumps(value), 'created_at': now, 'updated_at': now})
            self._audit(conn, org, project_id, 'action_updated' if old else 'action_created', ident, actor,
                {'old': {k: old.get(k) for k in value} if old else None, 'new': value})
            return self._get(conn, 'geo_action', org, ident, project_id)

    def list_actions(self, org, project_id, limit=20, offset=0):
        with self.connect() as conn:
            self._get(conn, 'geo_project', org, project_id)
            return self._page(conn, 'geo_action', org, project_id, limit, offset)

    def _batch_observations(self, conn, org, project, batch_id):
        return [self.apply_reviews(self._observation_detail(conn, decoded(row))) for row in conn.execute(
            'SELECT * FROM geo_observation WHERE org_id=? AND project_id=? AND batch_id=? ORDER BY question_version_id,condition_id,repeat_index', (org, project, batch_id))]

    def create_retest(self, org, action_id, payload, policy=None, actor='local'):
        actor = text_value(actor, '复测身份', 160, True)
        if not isinstance(payload, dict) or set(payload) - {'baseline_batch_id', 'idempotency_key', 'condition_ids'}:
            raise GeoError('复测字段错误')
        key = text_value(payload.get('idempotency_key'), '幂等标识', 160, True)
        with self.connect(True) as conn:
            action = self._get(conn, 'geo_action', org, action_id)
            project = action['project_id']
            executed = _when(action.get('executed_at'))
            if action.get('status') != 'executed' or not action.get('execution_evidence') or executed is None:
                raise GeoError('复测前须人工完成批准与执行证据记录')
            baseline = self._get(conn, 'geo_batch', org, payload.get('baseline_batch_id'), project)
            observations = self._batch_observations(conn, org, project, baseline['id'])
            if not any(_valid(x) for x in observations):
                raise GeoError('复测需要至少一条有效分析的真实基线回答')
            if any(_when(x.get('sampled_at')) and _when(x['sampled_at']) > executed for x in observations if _valid(x)):
                raise GeoError('基线采样不能晚于动作执行时间')
            frozen = deepcopy(baseline['manifest'])
            warnings = []
            if 'condition_ids' in payload:
                entries = payload['condition_ids']
                if not isinstance(entries, list) or not entries or len(entries) > 8 or any(not isinstance(x, str) for x in entries) or len(set(entries)) != len(entries):
                    raise GeoError('复测条件格式错误')
                conditions = [self._get(conn, 'geo_condition', org, ident, project) for ident in entries]
                if any(x['surface'] == 'doubao_app_manual' for x in conditions) and not all(x['surface'] == 'doubao_app_manual' for x in conditions):
                    raise GeoError('人工与API条件须独立复测')
                if sorted(x['condition_hash'] for x in conditions) != sorted(x['condition_hash'] for x in frozen['conditions']):
                    warnings.append('condition_mismatch')
                frozen['conditions'] = conditions
                frozen['manual'] = all(x['surface'] == 'doubao_app_manual' for x in conditions)
            request = {'question_version_ids': [x['id'] for x in frozen['questions']],
                'condition_ids': [x['id'] for x in frozen['conditions']], 'repeats': frozen['repeats'], 'idempotency_key': key}
            existing = conn.execute('SELECT * FROM geo_batch WHERE org_id=? AND project_id=? AND idempotency_key=?', (org, project, key)).fetchone()
            if existing:
                retest = conn.execute('SELECT * FROM geo_retest WHERE org_id=? AND project_id=? AND batch_id=?', (org, project, existing['id'])).fetchone()
                if not retest or retest['action_id'] != action_id or retest['baseline_batch_id'] != baseline['id']:
                    raise GeoError('复测幂等标识已用于其他任务', 'idempotency_conflict', 409)
            batch_id = self._create_batch(conn, org, project, request, policy or {}, actor, frozen=frozen)
            if existing:
                ident = retest['id']
            else:
                ident = uid('retest')
                value = {'warnings': warnings, 'executed_at': action['executed_at'], 'statement': 'observed_difference_not_causal'}
                self._insert(conn, 'geo_retest', {'id': ident, 'org_id': org, 'project_id': project,
                    'action_id': action_id, 'baseline_batch_id': baseline['id'], 'batch_id': batch_id,
                    'payload_json': dumps(value), 'created_at': stamp()})
                self._audit(conn, org, project, 'retest_created', ident, actor,
                    {'baseline_batch_id': baseline['id'], 'batch_id': batch_id, 'warnings': warnings})
        return self.get_retest(org, ident)

    def _retest_detail(self, conn, org, retest):
        baseline = self._get(conn, 'geo_batch', org, retest['baseline_batch_id'], retest['project_id'])
        current = self._get(conn, 'geo_batch', org, retest['batch_id'], retest['project_id'])
        action = self._get(conn, 'geo_action', org, retest['action_id'], retest['project_id'])
        left = self._batch_observations(conn, org, retest['project_id'], baseline['id'])
        right = self._batch_observations(conn, org, retest['project_id'], current['id'])
        warnings = list(retest.get('warnings') or [])
        lmanifest, rmanifest = baseline['manifest'], current['manifest']
        for field, warning in [('question_set_hash', 'question_mismatch'), ('entity_set_hash', 'entity_mismatch')]:
            if lmanifest[field] != rmanifest[field]: warnings.append(warning)
        if fingerprint(lmanifest['facts']) != fingerprint(rmanifest['facts']): warnings.append('fact_baseline_mismatch')
        if sorted(x['condition_hash'] for x in lmanifest['conditions']) != sorted(x['condition_hash'] for x in rmanifest['conditions']):
            warnings.append('condition_mismatch')
        if not any(_valid(x) for x in left): warnings.append('missing_valid_baseline')
        if not any(_valid(x) for x in right): warnings.append('missing_valid_retest')
        if current['status'] not in {'completed', 'completed_with_errors'}: warnings.append('retest_incomplete')
        executed = _when(action.get('executed_at'))
        if executed is None: warnings.append('execution_time_unknown')
        for rows, side in [(left, 'baseline'), (right, 'retest')]:
            valid = [x for x in rows if _valid(x)]
            if any(x.get('channel') == 'doubao_app_manual' and (
                x.get('condition', {}).get('mode') == 'unknown' or
                x.get('sample_metadata', {}).get('visible_search', 'unknown') == 'unknown') for x in valid):
                warnings.append('visible_search_unknown')
            if any(_when(x.get('sampled_at')) is None for x in valid): warnings.append(side + '_time_unknown')
            if executed and side == 'baseline' and any(_when(x.get('sampled_at')) and _when(x['sampled_at']) > executed for x in valid):
                warnings.append('baseline_after_execution')
            if executed and side == 'retest' and any(_when(x.get('sampled_at')) and _when(x['sampled_at']) <= executed for x in valid):
                warnings.append('sample_not_after_execution')
        def manual_metadata(rows):
            grouped = {}
            for obs in rows:
                if _valid(obs) and obs.get('channel') == 'doubao_app_manual':
                    key = (obs['question_version_id'], obs['condition']['condition_hash'])
                    fields = grouped.setdefault(key, {field: set() for field in ('new_session', 'personalization', 'visible_search')})
                    for field, values in fields.items():
                        values.add(obs.get('sample_metadata', {}).get(field, 'unknown'))
            return grouped
        left_manual, right_manual = manual_metadata(left), manual_metadata(right)
        if left_manual.keys() != right_manual.keys():
            warnings.append('manual_sample_scope_mismatch')
        for fields in [*left_manual.values(), *right_manual.values()]:
            for field, values in fields.items():
                if 'unknown' in values or None in values:
                    warnings.append(field + '_unknown')
                if len(values) > 1:
                    warnings.append(field + '_mismatch')
        for key in left_manual.keys() & right_manual.keys():
            for field in ('new_session', 'personalization', 'visible_search'):
                if left_manual[key][field] != right_manual[key][field]:
                    warnings.append(field + '_mismatch')
        def models(rows):
            groups = {}
            for obs in rows:
                if _valid(obs):
                    key = (obs['question_version_id'], obs['condition']['condition_hash'])
                    groups.setdefault(key, set()).add(obs.get('actual_model') or None)
            return groups
        lm, rm = models(left), models(right)
        if any(None in values for values in [*lm.values(), *rm.values()]): warnings.append('model_identity_unknown')
        if any(lm[k] != rm[k] for k in lm.keys() & rm.keys()): warnings.append('actual_model_mismatch')
        target, keys = lmanifest['target_key'], [x['key'] for x in lmanifest['entities']]
        lmetrics, rmetrics = compute_metrics(left, target, keys), compute_metrics(right, target, keys)
        warnings = list(dict.fromkeys(warnings))
        comparable = not warnings
        comparison = []
        if comparable:
            def group_key(group):
                return tuple(group[k] for k in ('channel', 'surface', 'mode', 'model', 'condition_hash', 'question_set_hash'))
            old_groups = {group_key(g): g for g in lmetrics['groups']}
            for group in rmetrics['groups']:
                old = old_groups.get(group_key(group))
                if old is None: continue
                result = {k: group[k] for k in ('channel', 'condition_hash', 'question_set_hash')}
                for metric, label in [('mention_rate', 'mention_percentage_point_difference'), ('recommendation_rate', 'recommendation_percentage_point_difference')]:
                    before, after = old['metrics'][metric], group['metrics'][metric]
                    result[label] = (after-before)*100 if before is not None and after is not None else None
                result.update(baseline_metrics=old['metrics'], current_metrics=group['metrics'], statement='observed_difference_not_causal')
                comparison.append(result)
        retest.update(comparable=comparable, warnings=warnings, comparison=comparison, status=current['status'],
            baseline_metrics=lmetrics, current_metrics=rmetrics, optimization_completed=False,
            manual=bool(current['manifest'].get('manual')))
        return retest

    def get_retest(self, org, retest_id):
        with self.connect() as conn:
            return self._retest_detail(conn, org, self._get(conn, 'geo_retest', org, retest_id))

    def list_retests(self, org, project_id, limit=20, offset=0):
        with self.connect() as conn:
            self._get(conn, 'geo_project', org, project_id)
            page = self._page(conn, 'geo_retest', org, project_id, limit, offset)
            page['items'] = [self._retest_detail(conn, org, x) for x in page['items']]
            return page

    def app_comparisons(self, org, project_id, limit=20, offset=0):
        with self.connect() as conn:
            self._get(conn, 'geo_project', org, project_id)
            page = self._page(conn, 'geo_observation', org, project_id, limit, offset,
                " AND channel='doubao_app_manual' AND json_extract(sample_metadata_json,'$.paired_observation_id') IS NOT NULL")
            items = []
            for row in page['items']:
                app = self.apply_reviews(self._observation_detail(conn, row))
                pair = self._get(conn, 'geo_observation', org, app['sample_metadata']['paired_observation_id'], project_id)
                api = self.apply_reviews(self._observation_detail(conn, pair))
                if api['channel'] == app['channel'] or api['question_version_id'] != app['question_version_id']:
                    continue
                warnings = []
                if not _valid(app): warnings.append('app_sample_invalid')
                if not _valid(api): warnings.append('api_sample_invalid')
                for field in ('new_session', 'personalization', 'visible_search'):
                    if app['sample_metadata'].get(field, 'unknown') == 'unknown': warnings.append(field + '_unknown')
                at, bt = _when(app.get('sampled_at')), _when(api.get('sampled_at'))
                distance = abs((at-bt).total_seconds()) if at and bt else None
                if distance is None: warnings.append('time_unknown')
                elif distance > 86400: warnings.append('samples_not_close_in_time')
                def entities(obs):
                    return {x['entity_key']: {k: x.get(k) for k in ('mentioned', 'recommended', 'rank')} for x in (obs.get('analysis') or {}).get('entities', [])}
                differences = {'app_entities': entities(app), 'api_entities': entities(api),
                    'app_fact_checks': (app.get('analysis') or {}).get('fact_checks', []), 'api_fact_checks': (api.get('analysis') or {}).get('fact_checks', []),
                    'app_citations': app['citations'], 'api_citations': api['citations']}
                items.append({'app_observation_id': app['id'], 'api_observation_id': api['id'],
                    'same_question': True, 'close_in_time': distance <= 86400 if distance is not None else None,
                    'time_distance_seconds': distance, 'differences': differences, 'warnings': warnings,
                    'statement': 'sample_difference_not_channel_equivalence'})
            page['items'] = items
            return page

    def get_screenshot(self, org, observation_id, screenshot_id):
        with self.connect() as conn:
            self._get(conn, 'geo_observation', org, observation_id)
            row = conn.execute('SELECT mime,content,sha256 FROM geo_screenshot WHERE org_id=? AND observation_id=? AND id=?',
                (org, observation_id, screenshot_id)).fetchone()
            if row is None:
                raise GeoError('截图不存在或不属于当前观测', 'not_found', 404)
            return {'mime': row['mime'], 'base64': base64.b64encode(row['content']).decode(), 'sha256': row['sha256']}

    def list_audit(self, org, project_id, limit=20, offset=0):
        with self.connect() as conn:
            self._get(conn, 'geo_project', org, project_id)
            return self._page(conn, 'geo_audit', org, project_id, limit, offset)
