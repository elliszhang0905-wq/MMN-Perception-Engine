"""Single-attempt, stateless Ark adapter with offline transport injection.

The worker owns retries, reservations and durable evidence. No API is called by
constructing this class. Production transport uses verified HTTPS, no proxies,
no redirects, a fixed official hostname and a two MiB response ceiling.
"""
import datetime as dt
import http.client
import ipaddress
import json
import math
import re
import socket
import ssl
import threading
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


DEFAULT_BASE_URL = 'https://ark.cn-beijing.volces.com/api/v3'
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
# Timed out DNS calls retain their slot until the resolver returns. They cannot
# accumulate unbounded daemon threads or open a connection after expiry.
_TRANSPORT_SLOTS = threading.BoundedSemaphore(4)
_SECRET_FIELDS = re.compile(r'^(?:x[_-])?(authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|cookie)$', re.I)
_URL = re.compile(r'https?://[^\s<>\[\]"\u3000\u3001\u3002\uff0c\uff09]+')


def _utc():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def _redact(value, secret):
    if isinstance(value, dict):
        return {str(k).replace(secret, '[REDACTED]') if secret else str(k):
                '[REDACTED]' if _SECRET_FIELDS.match(str(k)) else _redact(v, secret)
                for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v, secret) for v in value]
    if isinstance(value, str):
        value = value.replace(secret, '[REDACTED]') if secret else value
        return re.sub(r'(?i)Bearer\s+[^\s"<>]+', 'Bearer [REDACTED]', value)
    return value


def _usage(data=None):
    data = data if isinstance(data, dict) else {}
    result = {}
    aliases = {'input_tokens': 'prompt_tokens', 'output_tokens': 'completion_tokens'}
    for key in ('input_tokens', 'output_tokens', 'total_tokens'):
        value = data.get(key, data.get(aliases.get(key)))
        result[key] = value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
    for key in ('tool_usage', 'tool_usage_details', 'input_tokens_details', 'output_tokens_details'):
        result[key] = data.get(key) if isinstance(data.get(key), dict) else None
    missing = [k for k in ('input_tokens', 'output_tokens', 'total_tokens') if result[k] is None]
    result['missing_reason'] = 'Provider omitted or returned invalid ' + ', '.join(missing) if missing else None
    return result


def _normalized_url(url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            return None
        host = parsed.hostname.lower()
        if ':' in host:
            host = '[' + host + ']'
        port = parsed.port
        if port and (parsed.scheme.lower(), port) not in (('http', 80), ('https', 443)):
            host += ':' + str(port)
        query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                 if not k.lower().startswith('utm_') and k.lower() not in ('fbclid', 'gclid')]
        return urlunsplit((parsed.scheme.lower(), host, parsed.path or '/', urlencode(query), ''))
    except (ValueError, TypeError):
        return None


def _citation(url, title=None, source='structured', start=None, end=None):
    normalized = _normalized_url(url) if isinstance(url, str) else None
    if not normalized:
        return None
    return {'url': url, 'normalized_url': normalized, 'title': title,
            'source_type': source, 'start': start, 'end': end, 'verification_status': 'not_fetched'}


def _positive_counts(value):
    if isinstance(value, dict):
        return any(_positive_counts(v) for v in value.values())
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _visible_output(data, api_mode):
    """Return only visible answer blocks, direct annotations and search events."""
    parts, citations, events = [], [], []
    refused = False
    blocks = []
    if api_mode == 'chat':
        choices = data.get('choices') or []
        if choices and isinstance(choices[0], dict):
            message = choices[0].get('message') or {}
            if isinstance(message, dict):
                content = message.get('content')
                if isinstance(content, str):
                    blocks.append({'type': 'output_text', 'text': content})
                elif isinstance(content, list):
                    blocks.extend(content)
                refused = bool(message.get('refusal')) or choices[0].get('finish_reason') == 'content_filter'
    else:
        for item in data.get('output') or []:
            if not isinstance(item, dict):
                continue
            if item.get('type') == 'web_search_call':
                events.append(item)
            elif item.get('type') == 'message' and item.get('role', 'assistant') == 'assistant':
                blocks.extend(item.get('content') or [])
            elif item.get('type') == 'doubao_app_call':
                blocks.extend(item.get('blocks') or [])
    for block in blocks:
        if not isinstance(block, dict):
            continue
        kind = block.get('type')
        if kind in ('search', 'reasoning_search'):
            events.append(block)
        elif kind == 'refusal':
            refused = True
        elif kind in ('output_text', 'text') and isinstance(block.get('text'), str):
            text = block['text']
            offset = sum(len(p) for p in parts) + len(parts)
            parts.append(text)
            for annotation in block.get('annotations') or []:
                if isinstance(annotation, dict) and annotation.get('type') == 'url_citation':
                    start, end = annotation.get('start_index'), annotation.get('end_index')
                    entry = _citation(annotation.get('url'), annotation.get('title'),
                                      start=offset + start if isinstance(start, int) else None,
                                      end=offset + end if isinstance(end, int) else None)
                    if entry:
                        citations.append(entry)
    answer = '\n'.join(parts)
    for match in _URL.finditer(answer):
        url = match.group().rstrip('.,;:!?)}')
        entry = _citation(url, source='text_link', start=match.start(), end=match.start() + len(url))
        if entry:
            citations.append(entry)
    usage = data.get('usage') or {}
    if isinstance(usage, dict):
        for key in ('tool_usage', 'tool_usage_details'):
            tool = usage.get(key) or {}
            if isinstance(tool, dict):
                for name in ('web_search',):
                    if _positive_counts(tool.get(name)):
                        events.append({'type': 'usage_observation', 'source': key, 'tool': name, 'value': tool[name]})
                assistant = tool.get('doubao_app')
                if isinstance(assistant, dict):
                    for name in ('ai_search', 'reasoning_search'):
                        if _positive_counts(assistant.get(name)):
                            events.append({'type': 'usage_observation', 'source': key, 'tool': name, 'value': assistant[name]})
    return answer, citations, events, refused


def _decode_body(body, content_type):
    if isinstance(body, dict):
        if len(json.dumps(body, ensure_ascii=False).encode()) > MAX_RESPONSE_BYTES:
            raise OverflowError('Response body limit exceeded')
        return body, body, False
    if isinstance(body, bytes):
        if len(body) > MAX_RESPONSE_BYTES:
            raise OverflowError('Response body limit exceeded')
        body = body.decode('utf-8')
    if not isinstance(body, str):
        raise ValueError('Response body must be JSON or SSE')
    if len(body.encode()) > MAX_RESPONSE_BYTES:
        raise OverflowError('Response body limit exceeded')
    if 'text/event-stream' not in content_type and not body.lstrip().startswith(('event:', 'data:')):
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError('Expected a response object')
        return data, data, False
    events, final, partial = [], None, []
    for frame in re.split(r'\r?\n\r?\n', body):
        lines = [line[5:].lstrip() for line in frame.splitlines() if line.startswith('data:')]
        if not lines or '\n'.join(lines) == '[DONE]':
            continue
        try:
            event = json.loads('\n'.join(lines))
        except ValueError:
            events.append({'invalid_event': '\n'.join(lines)})
            continue
        if not isinstance(event, dict):
            events.append({'invalid_event': event})
            continue
        events.append(event)
        if event.get('type') in ('response.completed', 'response.failed', 'response.incomplete') and isinstance(event.get('response'), dict):
            final = event['response']
        if event.get('type') in ('response.output_text.delta', 'response.doubao_app_call.output_text.delta',
                                'response.doubao_app_call_output_text.delta'):
            if isinstance(event.get('delta'), str):
                partial.append(event['delta'])
    if final is None:
        final = {'status': 'incomplete', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': ''.join(partial)}]}]}
    damaged = any('invalid_event' in event for event in events)
    return final, {'events': events, 'response': final}, damaged or final.get('status') not in ('completed', 'failed')


def _stream_search_observations(raw):
    observations = []
    if not isinstance(raw, dict):
        return observations
    for event in raw.get('events', []):
        kind = event.get('type', '')
        if kind.startswith(('response.web_search_call.', 'response.doubao_app_call.search.',
                            'response.doubao_app_call.reasoning_search.',
                            'response.doubao_app_call_search.', 'response.doubao_app_call_reasoning_search.')):
            observations.append(event)
        for key in ('item', 'block'):
            item = event.get(key)
            if not isinstance(item, dict):
                continue
            if item.get('type') in ('web_search_call', 'search', 'reasoning_search'):
                observations.append(item)
            elif item.get('type') == 'doubao_app_call':
                observations.extend(block for block in item.get('blocks', [])
                                    if isinstance(block, dict) and block.get('type') in ('search', 'reasoning_search'))
    return observations


class _CancelledBeforeDispatch(Exception):
    pass


class _RequestControl:
    def __init__(self, timeout, cancel_event=None):
        self.deadline = time.monotonic() + timeout
        self.cancel_event = cancel_event
        self.stop = threading.Event()
        self.dispatched = False

    def remaining(self):
        if not self.dispatched and self.cancel_event is not None and self.cancel_event.is_set():
            raise _CancelledBeforeDispatch('Cancelled before request bytes were sent')
        remaining = self.deadline - time.monotonic()
        if self.stop.is_set() or remaining <= 0:
            raise TimeoutError('Total provider request deadline exceeded')
        return remaining


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Pin the validated public IP while preserving certificate hostname checks."""
    def __init__(self, *args, control, **kwargs):
        self.control = control
        super().__init__(*args, **kwargs)

    def connect(self):
        self.control.remaining()
        addresses = socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM)
        remaining = self.control.remaining()
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError('Official destination resolved to an unsafe address')
        sock = socket.create_connection((addresses[0][4][0], self.port), remaining)
        try:
            sock.settimeout(self.control.remaining())
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
            self.sock.settimeout(self.control.remaining())
        except BaseException:
            sock.close()
            raise

    def send(self, data):
        # Connect before the final pre-write cancellation/deadline gate.
        self.control.remaining()
        if self.sock is None:
            self.connect()
        self.sock.settimeout(self.control.remaining())
        self.control.dispatched = True
        return super().send(data)


def _https_transport(*, url, headers, payload, timeout, max_bytes, cancel_event=None, _control=None):
    parsed = urlsplit(url)
    control = _control or _RequestControl(timeout, cancel_event)
    conn = _PinnedHTTPSConnection(parsed.hostname, parsed.port or 443, timeout=timeout,
                                  context=ssl.create_default_context(), control=control)
    chunks, size = [], 0
    status, response_headers = 0, {}
    try:
        control.remaining()
        conn.request('POST', parsed.path, body=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers)
        conn.sock.settimeout(control.remaining())
        response = conn.getresponse()
        status, response_headers = response.status, dict(response.getheaders())
        while True:
            remaining = control.remaining()
            if conn.sock:
                conn.sock.settimeout(remaining)
            chunk = response.read1(min(65536, max_bytes + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > max_bytes:
                raise OverflowError('Response body limit exceeded')
        return {'status': status, 'headers': response_headers, 'body': b''.join(chunks)}
    except (socket.timeout, TimeoutError, http.client.IncompleteRead, OverflowError) as exc:
        return {'status': status, 'headers': response_headers, 'body': b''.join(chunks)[:max_bytes],
                'read_error': str(exc), 'error_class': 'timeout' if isinstance(exc, TimeoutError) else 'provider_error'}
    finally:
        conn.close()


class ArkProvider:
    def __init__(self, settings, *, transport=None):
        self.settings = dict(settings)
        self.transport = transport or _https_transport
        self._production_transport = transport is None

    def capabilities(self, condition):
        def declared(name):
            value = self.settings.get('supports_' + name)
            return value if isinstance(value, bool) else None
        supplied = condition.get('capabilities') or {}
        return {'temperature': declared('temperature'), 'seed': declared('seed'),
                'search': supplied.get('search') if isinstance(supplied, dict) and isinstance(supplied.get('search'), bool) else None,
                'structured_citations': None}

    def _dispatch(self, **request):
        """Share a deadline/stop signal and bound all outstanding transports."""
        control = _RequestControl(request['timeout'], request.get('cancel_event'))
        if not _TRANSPORT_SLOTS.acquire(blocking=False):
            raise TimeoutError('Outstanding provider transport limit reached; no new request dispatched')
        slots = _TRANSPORT_SLOTS
        completed = threading.Event()
        outcome = []
        def run():
            try:
                control.remaining()
                if self._production_transport:
                    outcome.append((True, self.transport(**request, _control=control)))
                else:
                    # An injected transport owns its I/O; record dispatch before
                    # entering it, and hold its slot until it actually finishes.
                    control.dispatched = True
                    outcome.append((True, self.transport(**request)))
            except Exception as exc:
                outcome.append((False, exc))
            finally:
                slots.release()
                completed.set()
        try:
            threading.Thread(target=run, name='geo-ark-single-request', daemon=True).start()
        except Exception:
            slots.release()
            raise
        while not completed.is_set():
            if control.cancel_event is not None and control.cancel_event.is_set() and not control.dispatched:
                control.stop.set()
                raise _CancelledBeforeDispatch('Cancelled before request bytes were sent')
            remaining = control.deadline - time.monotonic()
            if remaining <= 0:
                control.stop.set()
                raise TimeoutError('Total provider request deadline exceeded; billing is uncertain')
            completed.wait(min(remaining, 0.01))
        ok, value = outcome[0]
        if not ok:
            raise value
        return value

    def _request(self, question, condition):
        key = self.settings.get('api_key')
        model = condition.get('model') or self.settings.get('model')
        base = self.settings.get('base_url') or DEFAULT_BASE_URL
        parsed = urlsplit(base)
        if (parsed.scheme != 'https' or parsed.hostname != 'ark.cn-beijing.volces.com'
                or parsed.port not in (None, 443) or parsed.username or parsed.password
                or parsed.path.rstrip('/') != '/api/v3' or parsed.query or parsed.fragment):
            raise ValueError('Only the trusted official Ark HTTPS base URL is allowed')
        if not isinstance(key, str) or not key.strip() or not isinstance(model, str) or not model.strip():
            raise ValueError('Ark credential and configured model are required')
        api = condition.get('api_mode') or self.settings.get('api_mode') or 'responses'
        surface = condition.get('surface', 'ark_model_api')
        mode = condition.get('mode', 'non_search')
        if surface not in ('ark_model_api', 'ark_assistant_api') or api not in ('chat', 'responses', 'assistant'):
            raise ValueError('This surface requires manual sampling or is unsupported')
        assistant = surface == 'ark_assistant_api'
        if (assistant and api == 'chat') or (api == 'assistant' and not assistant):
            raise ValueError('Assistant surface requires the assistant Responses API')
        if mode not in ('non_search', 'search_enabled') or (mode == 'search_enabled' and api == 'chat'):
            raise ValueError('Chat completion does not support search sampling')
        text = question.get('text')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('A nonempty question is required')
        timeout = condition.get('timeout_seconds', 30)
        maximum = condition.get('max_output_tokens', 2048)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 120:
            raise ValueError('timeout_seconds must be greater than zero and at most 120')
        if isinstance(maximum, bool) or not isinstance(maximum, int) or not 0 < maximum <= 32768:
            raise ValueError('max_output_tokens must be 1 through 32768')
        payload = {'model': model, 'store': False, 'stream': False}
        system = condition.get('system_prompt') or ''
        if not isinstance(system, str):
            raise ValueError('system_prompt must be text')
        if api == 'chat':
            payload['messages'] = ([{'role': 'system', 'content': system}] if system else []) + [{'role': 'user', 'content': text}]
            payload['max_tokens'] = maximum
            endpoint = '/chat/completions'
        else:
            payload['input'] = [{'role': 'user', 'content': [{'type': 'input_text', 'text': text}]}]
            if system:
                payload['instructions'] = system
            payload['max_output_tokens'] = maximum
            endpoint = '/responses'
        capabilities = self.capabilities(condition)
        if mode == 'search_enabled' and capabilities['search'] is False:
            raise ValueError('Search capability is explicitly unsupported')
        for parameter in ('temperature', 'seed'):
            value = condition.get(parameter)
            if capabilities[parameter] is True and value is not None:
                if parameter == 'temperature' and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 2):
                    raise ValueError('temperature must be within 0 through 2')
                if parameter == 'seed' and (isinstance(value, bool) or not isinstance(value, int)):
                    raise ValueError('seed must be an integer')
                payload[parameter] = value
        headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
        if assistant:
            headers['ark-beta-doubao-app'] = 'true'
            feature = 'ai_search' if mode == 'search_enabled' else 'chat'
            payload['tools'] = [{'type': 'doubao_app', 'feature': {feature: {'type': 'enabled'}}}]
        elif mode == 'search_enabled':
            payload['tools'] = [{'type': 'web_search'}]
        return base.rstrip('/') + endpoint, headers, payload, float(timeout), api

    def sample(self, question, condition, cancel_event=None):
        secret = self.settings.get('api_key')
        secret = secret if isinstance(secret, str) else ''
        result = {'status': 'failed', 'answer': '', 'raw_response': None,
                  'request_id': None, 'actual_model': None, 'usage': _usage(),
                  'search_requested': condition.get('mode') == 'search_enabled',
                  'search_observed': False, 'search_events': [], 'citations': [],
                  'capabilities': self.capabilities(condition), 'error_class': None,
                  'error': None, 'retry_after': None, 'billing_uncertain': False,
                  'started_at': _utc(), 'finished_at': None}
        def finish():
            if cancel_event is not None and cancel_event.is_set():
                result.update(status='cancelled', error_class='cancelled',
                              error='Cancelled; available provider evidence and billing uncertainty retained')
            result['finished_at'] = _utc()
            return _redact(result, secret)
        if cancel_event is not None and cancel_event.is_set():
            result.update(status='cancelled', error_class='cancelled', error='Cancelled before dispatch')
            return finish()
        try:
            url, headers, payload, timeout, api = self._request(question, condition)
        except (ValueError, TypeError) as exc:
            result.update(error_class='configuration_missing', error=str(exc))
            return finish()
        try:
            received = self._dispatch(url=url, headers=headers, payload=payload, timeout=timeout,
                                      max_bytes=MAX_RESPONSE_BYTES, cancel_event=cancel_event)
        except _CancelledBeforeDispatch as exc:
            result.update(status='cancelled', error_class='cancelled', error=str(exc), billing_uncertain=False)
            return finish()
        except (socket.timeout, TimeoutError) as exc:
            result.update(status='uncertain', error_class='timeout', error=str(exc), billing_uncertain=True)
            return finish()
        except Exception as exc:
            result.update(status='uncertain', error_class='provider_error', error=str(exc), billing_uncertain=True)
            return finish()
        try:
            if not isinstance(received, dict):
                raise ValueError('Invalid transport response envelope')
            status = int(received.get('status', 0))
            response_headers = {str(k).lower(): str(v) for k, v in received.get('headers', {}).items()}
            result['request_id'] = response_headers.get('x-request-id') or response_headers.get('x-tt-logid')
            body = received.get('body', b'')
            try:
                data, raw, incomplete = _decode_body(body, response_headers.get('content-type', ''))
            except (ValueError, UnicodeError) as exc:
                result['raw_response'] = {'unparsed_body': body.decode('utf-8', errors='replace') if isinstance(body, bytes) else body}
                result.update(error_class='parse_error', error=str(exc), billing_uncertain=True)
                if received.get('read_error'):
                    result.update(status='uncertain', error_class=received.get('error_class', 'provider_error'), error=received['read_error'])
                elif status >= 400:
                    self._http_error(result, status, {}, response_headers)
                return finish()
            result['raw_response'] = raw
            result['request_id'] = result['request_id'] or data.get('request_id') or data.get('id')
            result['actual_model'] = data.get('model')
            result['usage'] = _usage(data.get('usage'))
            result['billing_uncertain'] = bool(result['usage']['missing_reason'])
            answer, citations, events, refused = _visible_output(data, api)
            for event in _stream_search_observations(raw):
                if event not in events:
                    events.append(event)
            result.update(answer=answer, citations=citations, search_events=events, search_observed=bool(events))
            if received.get('read_error') or incomplete:
                result.update(status='uncertain', error_class=received.get('error_class', 'provider_error'),
                              error=received.get('read_error', 'Provider response did not complete'), billing_uncertain=True)
            elif status < 200 or status >= 300:
                self._http_error(result, status, data, response_headers)
            elif api != 'chat' and data.get('status') not in ('completed', 'failed'):
                result.update(status='uncertain', error_class='provider_error',
                              error='Provider response did not complete', billing_uncertain=True)
            elif data.get('error') or data.get('status') == 'failed':
                result.update(status='failed', error_class='provider_error', error=str(data.get('error') or 'Provider response failed'))
            elif refused:
                result['status'] = 'refused'
            elif api == 'chat' and (not data.get('choices') or data['choices'][0].get('finish_reason') != 'stop'):
                result.update(status='uncertain', error_class='provider_error', error='Chat response did not finish', billing_uncertain=True)
            elif not answer.strip():
                result['status'] = 'empty'
            else:
                result['status'] = 'completed'
        except OverflowError as exc:
            result.update(status='uncertain', error_class='provider_error', error=str(exc), billing_uncertain=True)
        except Exception as exc:
            result.update(status='failed', error_class='parse_error', error=str(exc), billing_uncertain=True)
        if cancel_event is not None and cancel_event.is_set():
            result.update(status='cancelled', error_class='cancelled', error='Cancelled during dispatch; available provider evidence retained')
        return finish()

    @staticmethod
    def _http_error(result, status, data, headers):
        error = data.get('error') or {}
        hint = json.dumps(error, ensure_ascii=False).lower()
        quota = any(term in hint for term in ('quota', 'insufficientbalance', 'insufficient_balance'))
        category = 'quota' if quota else {401: 'authentication', 403: 'permission', 429: 'rate_limit'}.get(status, 'provider_error')
        result.update(status='failed', error_class=category, error=str(error or 'HTTP ' + str(status)))
        if status in (401, 403) or category == 'quota':
            result['billing_uncertain'] = False
        if (status == 429 and not quota) or status in (500, 502, 503, 504):
            value = headers.get('retry-after')
            try:
                result['retry_after'] = max(0, float(value)) if value is not None and math.isfinite(float(value)) else None
            except (ValueError, TypeError):
                try:
                    from email.utils import parsedate_to_datetime
                    retry_time = parsedate_to_datetime(value)
                    result['retry_after'] = max(0, (retry_time - dt.datetime.now(dt.timezone.utc)).total_seconds())
                except (ValueError, TypeError):
                    result['retry_after'] = None
