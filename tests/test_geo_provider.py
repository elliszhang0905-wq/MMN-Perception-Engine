"""Offline Ark protocol fixtures; no endpoint or credential is contacted."""
import importlib.util
import json
import socket
import threading
import time
import unittest
from unittest.mock import Mock, patch
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / 'geo' / 'provider.py'
if MODULE.exists():
    spec = importlib.util.spec_from_file_location('geo_provider_under_test', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ArkProvider = module.ArkProvider
else:
    ArkProvider = None


KEY = 'offline-secret-key'
SETTINGS = {'api_key': KEY, 'model': 'configured-test-model', 'api_mode': 'responses'}
CONDITION = {'surface': 'ark_model_api', 'api_mode': 'responses',
             'mode': 'non_search', 'max_output_tokens': 100, 'timeout_seconds': 2,
             'system_prompt': 'Neutral assistant', 'temperature': 0.3, 'seed': 17}
FIELDS = {'status', 'answer', 'raw_response', 'request_id', 'actual_model', 'usage',
          'search_requested', 'search_observed', 'search_events', 'citations',
          'capabilities', 'error_class', 'error', 'retry_after', 'billing_uncertain',
          'started_at', 'finished_at'}


def response(text='answer', **extra):
    return {'id': 'response-id', 'status': 'completed', 'model': 'actual-fixture-model',
            'output': [{'type': 'message', 'role': 'assistant', 'content': [
                {'type': 'output_text', 'text': text, 'annotations': []}]}],
            'usage': {'input_tokens': 5, 'output_tokens': 3, 'total_tokens': 8}, **extra}


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ArkProvider, 'ArkProvider behavior has not been implemented')
        self.calls = []

    def provider(self, body=None, status=200, headers=None, settings=None, side_effect=None):
        def transport(**request):
            self.calls.append(request)
            if side_effect:
                return side_effect(request)
            return {'status': status, 'headers': headers or {},
                    'body': response() if body is None else body}
        return ArkProvider({**SETTINGS, **(settings or {})}, transport=transport)

    def sample(self, provider, **changes):
        return provider.sample({'text': 'Which vehicle suits a family?'},
                               {**CONDITION, **changes})

    def test_fixed_result_and_stateless_responses_request(self):
        result = self.sample(self.provider())
        self.assertEqual(set(result), FIELDS)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['actual_model'], 'actual-fixture-model')
        self.assertEqual(len(self.calls), 1)
        call = self.calls[0]
        self.assertEqual(call['url'], 'https://ark.cn-beijing.volces.com/api/v3/responses')
        self.assertFalse(call['payload']['store'])
        self.assertNotIn('previous_response_id', call['payload'])
        self.assertNotIn('temperature', call['payload'])
        self.assertNotIn('seed', call['payload'])
        self.assertEqual(result['citations'], [])
        self.assertTrue(result['started_at'].endswith('Z'))
        self.assertIsNone(result['capabilities']['temperature'])

    def test_explicit_temperature_and_seed_support(self):
        p = self.provider(settings={'supports_temperature': True, 'supports_seed': True})
        self.sample(p)
        self.assertEqual(self.calls[0]['payload']['temperature'], 0.3)
        self.assertEqual(self.calls[0]['payload']['seed'], 17)

    def test_search_request_without_event_is_not_observed(self):
        result = self.sample(self.provider(), mode='search_enabled')
        self.assertTrue(result['search_requested'])
        self.assertFalse(result['search_observed'])
        self.assertEqual(self.calls[0]['payload']['tools'], [{'type': 'web_search'}])

    def test_search_events_and_usage_are_separate_from_citations(self):
        body = response()
        body['output'].insert(0, {'type': 'web_search_call', 'status': 'completed',
                                  'action': {'query': 'cars'}})
        result = self.sample(self.provider(body), mode='search_enabled')
        self.assertTrue(result['search_observed'])
        self.assertEqual(len(result['search_events']), 1)
        self.assertEqual(result['citations'], [])

    def test_search_usage_observation(self):
        body = response()
        body['usage']['tool_usage'] = {'web_search': 1}
        result = self.sample(self.provider(body))
        self.assertTrue(result['search_observed'])
        self.assertFalse(result['search_requested'])

    def test_structured_and_text_urls_have_distinct_provenance(self):
        body = response('Read https://EXAMPLE.com/a?utm_source=x#part')
        body['output'][0]['content'][0]['annotations'] = [
            {'type': 'url_citation', 'url': 'https://example.com/source', 'title': 'Source',
             'start_index': 0, 'end_index': 4}]
        result = self.sample(self.provider(body))
        self.assertEqual([x['source_type'] for x in result['citations']], ['structured', 'text_link'])
        self.assertEqual(result['citations'][0]['start'], 0)
        self.assertEqual(result['citations'][1]['normalized_url'], 'https://example.com/a')
        self.assertTrue(all(x['verification_status'] == 'not_fetched' for x in result['citations']))

    def test_assistant_request_and_visible_final_text(self):
        body = response()
        body['output'] = [{'type': 'doubao_app_call', 'blocks': [
            {'type': 'reasoning_text', 'reasoning_text': 'hidden reasoning'},
            {'type': 'search', 'queries': ['cars'], 'results': [{'url': 'https://example.com/search'}]},
            {'type': 'output_text', 'text': 'Visible final'}]}]
        result = self.sample(self.provider(body), surface='ark_assistant_api', api_mode='assistant',
                             mode='search_enabled')
        self.assertEqual(result['answer'], 'Visible final')
        self.assertTrue(result['search_observed'])
        self.assertEqual(result['citations'], [])
        self.assertEqual(self.calls[0]['headers']['ark-beta-doubao-app'], 'true')
        self.assertEqual(self.calls[0]['payload']['tools'],
                         [{'type': 'doubao_app', 'feature': {'ai_search': {'type': 'enabled'}}}])

    def test_assistant_call_does_not_itself_prove_search(self):
        body = response(output=[{'type': 'doubao_app_call', 'blocks': [{'type': 'output_text', 'text': 'Hi'}]}])
        result = self.sample(self.provider(body), surface='ark_assistant_api', api_mode='assistant')
        self.assertFalse(result['search_observed'])
        self.assertEqual(self.calls[0]['payload']['tools'][0]['feature'], {'chat': {'type': 'enabled'}})

    def test_completed_sse_uses_final_object_and_preserves_events(self):
        body = 'event: response.completed\ndata: ' + json.dumps({'type': 'response.completed', 'response': response('Final')}) + '\n\ndata: [DONE]\n\n'
        result = self.sample(self.provider(body, headers={'Content-Type': 'text/event-stream'}))
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['answer'], 'Final')
        self.assertEqual(len(result['raw_response']['events']), 1)

    def test_incomplete_stream_is_uncertain_and_not_retried(self):
        body = 'data: {"type":"response.output_text.delta","delta":"partial"}\n\n'
        result = self.sample(self.provider(body, headers={'Content-Type': 'text/event-stream'}))
        self.assertEqual(result['status'], 'uncertain')
        self.assertEqual(result['answer'], 'partial')
        self.assertTrue(result['billing_uncertain'])
        self.assertEqual(len(self.calls), 1)

    def test_timeout_is_uncertain(self):
        def timeout(_):
            raise socket.timeout('timeout ' + KEY)
        result = self.sample(self.provider(side_effect=timeout))
        self.assertEqual(result['status'], 'uncertain')
        self.assertEqual(result['error_class'], 'timeout')
        self.assertNotIn(KEY, json.dumps(result))
        self.assertEqual(len(self.calls), 1)

    def test_http_error_classes_and_retry_after_without_retry(self):
        for status, category in [(401, 'authentication'), (403, 'permission'),
                                 (429, 'rate_limit'), (503, 'provider_error')]:
            with self.subTest(status=status):
                result = self.sample(self.provider({'error': {'message': 'err ' + KEY}}, status=status,
                                                    headers={'Retry-After': '12', 'X-Request-Id': 'http-id'}))
                self.assertEqual(result['error_class'], category)
                self.assertEqual(result['request_id'], 'http-id')
                self.assertNotIn(KEY, json.dumps(result))
                self.assertEqual(result['retry_after'], 12 if status in (429, 503) else None)

    def test_quota_error(self):
        result = self.sample(self.provider({'error': {'code': 'InsufficientQuota', 'message': 'quota'}}, status=429))
        self.assertEqual(result['error_class'], 'quota')

    def test_body_secret_fields_and_echoes_are_redacted(self):
        body = response('echo ' + KEY)
        body['api_key'] = 'different-secret'
        result = self.sample(self.provider(body))
        self.assertNotIn(KEY, json.dumps(result))
        self.assertNotIn('different-secret', json.dumps(result))

    def test_missing_usage_is_null_with_reason(self):
        body = response()
        del body['usage']
        result = self.sample(self.provider(body))
        self.assertIsNone(result['usage']['total_tokens'])
        self.assertTrue(result['usage']['missing_reason'])
        self.assertTrue(result['billing_uncertain'])

    def test_header_request_id_preferred_to_response_id(self):
        result = self.sample(self.provider(headers={'x-request-id': 'header-id'}))
        self.assertEqual(result['request_id'], 'header-id')

    def test_missing_key_or_model_has_no_network(self):
        for settings in [{'api_key': ''}, {'model': ''}]:
            result = self.sample(self.provider(settings=settings))
            self.assertEqual(result['error_class'], 'configuration_missing')
        self.assertEqual(self.calls, [])

    def test_forbidden_destinations_even_with_injected_transport(self):
        for url in ['http://ark.cn-beijing.volces.com/api/v3', 'https://127.0.0.1/api/v3',
                    'https://evil.example/api/v3', 'https://ark.cn-beijing.volces.com.evil.example/api/v3',
                    'https://user:pass@ark.cn-beijing.volces.com/api/v3']:
            result = self.sample(self.provider(settings={'base_url': url}))
            self.assertEqual(result['error_class'], 'configuration_missing')
        self.assertEqual(self.calls, [])

    def test_chat_is_stateless_and_cannot_request_search(self):
        body = {'model': 'chat-fixture', 'choices': [{'message': {'content': 'Chat answer'}, 'finish_reason': 'stop'}]}
        p = self.provider(body)
        result = self.sample(p, api_mode='chat')
        self.assertEqual(result['answer'], 'Chat answer')
        self.assertTrue(self.calls[0]['url'].endswith('/chat/completions'))
        self.assertFalse(self.calls[0]['payload']['store'])
        result = self.sample(p, api_mode='chat', mode='search_enabled')
        self.assertEqual(result['error_class'], 'configuration_missing')
        self.assertEqual(len(self.calls), 1)

    def test_manual_surface_has_no_network(self):
        result = self.sample(self.provider(), surface='doubao_app_manual', api_mode='manual')
        self.assertEqual(result['error_class'], 'configuration_missing')
        self.assertEqual(self.calls, [])

    def test_cancel_before_send(self):
        event = threading.Event()
        event.set()
        result = self.provider().sample({'text': 'test'}, CONDITION, event)
        self.assertEqual(result['status'], 'cancelled')
        self.assertFalse(result['billing_uncertain'])
        self.assertEqual(self.calls, [])

    def test_cancel_in_flight_keeps_real_evidence_and_usage(self):
        event = threading.Event()
        def finish(_):
            event.set()
            return {'status': 200, 'headers': {}, 'body': response('Real answer')}
        result = self.provider(side_effect=finish).sample({'text': 'test'}, CONDITION, event)
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(result['answer'], 'Real answer')
        self.assertEqual(result['usage']['total_tokens'], 8)
        self.assertFalse(result['billing_uncertain'])

    def test_invalid_json_and_non_object_are_parse_errors(self):
        for body in ['<html>oops</html>', '[]']:
            result = self.sample(self.provider(body))
            self.assertEqual(result['error_class'], 'parse_error')
            self.assertTrue(result['billing_uncertain'])

    def test_response_limit_is_uncertain(self):
        result = self.sample(self.provider('x' * (2 * 1024 * 1024 + 1)))
        self.assertEqual(result['status'], 'uncertain')
        self.assertTrue(result['billing_uncertain'])

    def test_empty_refused_incomplete_and_provider_failed(self):
        for body, status in [(response(''), 'empty'),
                             (response(output=[{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'No'}]}]), 'refused'),
                             (response(status='incomplete'), 'uncertain'),
                             (response(status='failed', error={'message': 'failed'}), 'failed')]:
            self.assertEqual(self.sample(self.provider(body))['status'], status)

    def test_unknown_transport_exception_does_not_expose_secrets(self):
        def fail(_):
            raise RuntimeError('danger ' + KEY)
        result = self.sample(self.provider(side_effect=fail))
        self.assertEqual(result['error_class'], 'provider_error')
        self.assertNotIn(KEY, json.dumps(result))

    def test_redirect_is_failed_without_following(self):
        result = self.sample(self.provider(response('redirect answer'), status=302,
                                          headers={'Location': 'https://evil.example'}))
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error_class'], 'provider_error')
        self.assertEqual(len(self.calls), 1)

    def test_malformed_stream_cannot_be_completed(self):
        body = 'data: broken-json\n\ndata: ' + json.dumps({'type': 'response.completed', 'response': response()}) + '\n\n'
        result = self.sample(self.provider(body, headers={'content-type': 'text/event-stream'}))
        self.assertEqual(result['status'], 'uncertain')
        self.assertTrue(result['billing_uncertain'])

    def test_declared_search_unsupported_has_no_network(self):
        result = self.sample(self.provider(), mode='search_enabled', capabilities={'search': False})
        self.assertEqual(result['error_class'], 'configuration_missing')
        self.assertEqual(self.calls, [])

    def test_missing_response_terminal_status_is_uncertain(self):
        body = response()
        del body['status']
        result = self.sample(self.provider(body))
        self.assertEqual(result['status'], 'uncertain')

    def test_transport_deadline_bounds_total_wait(self):
        done = threading.Event()
        def delayed(_):
            done.wait(1)
            return {'status': 200, 'headers': {}, 'body': response()}
        try:
            before = time.monotonic()
            result = self.sample(self.provider(side_effect=delayed), timeout_seconds=0.02)
            self.assertLess(time.monotonic() - before, 0.3)
            self.assertEqual(result['status'], 'uncertain')
            self.assertEqual(result['error_class'], 'timeout')
            self.assertEqual(len(self.calls), 1)
        finally:
            done.set()

    def test_partial_read_with_evidence_is_uncertain(self):
        def partial(_):
            return {'status': 200, 'headers': {'X-Request-Id': 'partial-id'},
                    'body': response('available'), 'read_error': 'truncated', 'error_class': 'provider_error'}
        result = self.sample(self.provider(side_effect=partial))
        self.assertEqual(result['status'], 'uncertain')
        self.assertEqual(result['answer'], 'available')
        self.assertEqual(result['request_id'], 'partial-id')

    def test_chat_content_filter_is_refused(self):
        body = {'choices': [{'message': {'content': ''}, 'finish_reason': 'content_filter'}]}
        result = self.sample(self.provider(body), api_mode='chat')
        self.assertEqual(result['status'], 'refused')

    def test_incomplete_stream_retains_search_observation(self):
        event = {'type': 'response.output_item.added', 'item': {
            'type': 'web_search_call', 'id': 'ws-event', 'status': 'in_progress'}}
        body = 'data: ' + json.dumps(event) + '\n\n'
        result = self.sample(self.provider(body, headers={'content-type': 'text/event-stream'}))
        self.assertEqual(result['status'], 'uncertain')
        self.assertTrue(result['search_observed'])
        self.assertEqual(result['search_events'][0]['id'], 'ws-event')

    def test_assistant_stream_search_block_is_observed(self):
        event = {'type': 'response.doubao_app_call_block.added',
                 'block': {'type': 'search', 'queries': ['cars'], 'results': []}}
        body = 'data: ' + json.dumps(event) + '\n\n'
        result = self.sample(self.provider(body), api_mode='assistant', surface='ark_assistant_api')
        self.assertTrue(result['search_observed'])
        self.assertEqual(result['citations'], [])

    def test_cancelled_timeout_still_records_billing_uncertain(self):
        event = threading.Event()
        def timeout(_):
            event.set()
            raise socket.timeout('timeout')
        result = self.provider(side_effect=timeout).sample({'text': 'test'}, CONDITION, event)
        self.assertEqual(result['status'], 'cancelled')
        self.assertTrue(result['billing_uncertain'])

    def test_sensitive_header_field_redacted(self):
        body = response()
        body['request_headers'] = {'X-API-Key': 'unknown-echo-secret'}
        result = self.sample(self.provider(body))
        self.assertNotIn('unknown-echo-secret', json.dumps(result))

    def test_official_underscore_assistant_stream_names(self):
        for name in ('search', 'reasoning_search'):
            body = '\n\n'.join('data: ' + json.dumps(event) for event in [
                {'type': 'response.doubao_app_call_output_text.delta', 'delta': 'visible partial'},
                {'type': 'response.doubao_app_call_' + name + '.in_progress', 'item_id': 'search1'},
                {'type': 'response.doubao_app_call_reasoning_text.delta', 'delta': 'hidden'}]) + '\n\n'
            result = self.sample(self.provider(body), surface='ark_assistant_api',
                                 api_mode='assistant', mode='search_enabled')
            self.assertEqual(result['status'], 'uncertain')
            self.assertEqual(result['answer'], 'visible partial')
            self.assertTrue(result['search_observed'])
            self.assertEqual(result['search_events'][0]['item_id'], 'search1')

    def test_read_timeout_dominates_retryable_http_status(self):
        for status in (429, 503):
            def timeout(_):
                return {'status': status, 'headers': {'X-Request-Id': 'timeout-id', 'Retry-After': '10'},
                        'body': {'error': {'message': 'busy'}},
                        'read_error': 'Response deadline exceeded', 'error_class': 'timeout'}
            result = self.sample(self.provider(side_effect=timeout))
            self.assertEqual(result['status'], 'uncertain')
            self.assertEqual(result['error_class'], 'timeout')
            self.assertTrue(result['billing_uncertain'])
            self.assertEqual(result['request_id'], 'timeout-id')
            self.assertIsNone(result['retry_after'])

    def test_delayed_dns_never_connects_after_deadline_or_cancel(self):
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        cancel = threading.Event()
        def delayed_dns(*args, **kwargs):
            entered.set()
            release.wait(1)
            finished.set()
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))]
        with patch.object(module.socket, 'getaddrinfo', side_effect=delayed_dns), \
                patch.object(module.socket, 'create_connection', side_effect=RuntimeError('no actual network')) as connect:
            try:
                result = ArkProvider(SETTINGS).sample({'text': 'offline'},
                                                       {**CONDITION, 'timeout_seconds': 0.03}, cancel)
                self.assertTrue(entered.is_set())
                self.assertEqual(result['status'], 'uncertain')
                cancel.set()
                release.set()
                self.assertTrue(finished.wait(0.5))
                time.sleep(0.02)
                connect.assert_not_called()
            finally:
                release.set()

    def test_chat_handoff_and_unknown_finish_reasons_are_uncertain(self):
        for reason in ('tool_calls', 'function_call', 'unknown', 'length', None):
            body = {'choices': [{'message': {'content': 'Tool starting'}, 'finish_reason': reason}],
                    'usage': {'prompt_tokens': 2, 'completion_tokens': 2, 'total_tokens': 4}}
            result = self.sample(self.provider(body), api_mode='chat')
            self.assertEqual(result['status'], 'uncertain')
            self.assertEqual(result['answer'], 'Tool starting')
            self.assertEqual(result['usage']['total_tokens'], 4)

    def test_empty_chat_handoff_is_also_uncertain(self):
        body = {'choices': [{'message': {'content': ''}, 'finish_reason': 'tool_calls'}]}
        self.assertEqual(self.sample(self.provider(body), api_mode='chat')['status'], 'uncertain')

    def test_cancel_during_dns_never_dispatches(self):
        entered, release = threading.Event(), threading.Event()
        cancel = threading.Event()
        def delayed_dns(*args, **kwargs):
            entered.set()
            release.wait(1)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))]
        def cancel_after_entry():
            entered.wait(0.5)
            cancel.set()
        with patch.object(module.socket, 'getaddrinfo', side_effect=delayed_dns), \
                patch.object(module.socket, 'create_connection') as connect:
            canceller = threading.Thread(target=cancel_after_entry)
            canceller.start()
            try:
                result = ArkProvider(SETTINGS).sample({'text': 'offline'}, CONDITION, cancel)
                self.assertEqual(result['status'], 'cancelled')
                self.assertFalse(result['billing_uncertain'])
                release.set()
                canceller.join(0.5)
                time.sleep(0.02)
                connect.assert_not_called()
            finally:
                release.set()

    def test_cancellation_after_connect_blocks_tls(self):
        cancel = threading.Event()
        sock = Mock()
        control = module._RequestControl(1, cancel)
        context = Mock()
        def connect(*args, **kwargs):
            cancel.set()
            return sock
        connection = module._PinnedHTTPSConnection('ark.cn-beijing.volces.com', control=control)
        connection._context = context
        with patch.object(module.socket, 'getaddrinfo', return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))]), \
                patch.object(module.socket, 'create_connection', side_effect=connect):
            with self.assertRaises(module._CancelledBeforeDispatch):
                connection.connect()
        context.wrap_socket.assert_not_called()
        sock.close.assert_called_once()

    def test_cancellation_after_tls_blocks_request_write(self):
        cancel = threading.Event()
        sock, tls = Mock(), Mock()
        control = module._RequestControl(1, cancel)
        connection = module._PinnedHTTPSConnection('ark.cn-beijing.volces.com', control=control)
        def wrap(*args, **kwargs):
            cancel.set()
            return tls
        connection._context = Mock(wrap_socket=Mock(side_effect=wrap))
        try:
            with patch.object(module.socket, 'getaddrinfo', return_value=[
                    (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))]), \
                    patch.object(module.socket, 'create_connection', return_value=sock):
                with self.assertRaises(module._CancelledBeforeDispatch):
                    connection.request('POST', '/api/v3/responses', body=b'offline')
            tls.sendall.assert_not_called()
            self.assertFalse(control.dispatched)
        finally:
            connection.close()

    def test_outstanding_transport_count_is_bounded_after_timeout(self):
        gate, ended = threading.Event(), threading.Event()
        def delayed(_):
            try:
                gate.wait(1)
                return {'status': 200, 'headers': {}, 'body': response()}
            finally:
                ended.set()
        with patch.object(module, '_TRANSPORT_SLOTS', threading.BoundedSemaphore(1)):
            try:
                first = self.sample(self.provider(side_effect=delayed), timeout_seconds=0.02)
                second = self.sample(self.provider(), timeout_seconds=0.02)
                self.assertEqual(first['status'], 'uncertain')
                self.assertEqual(second['status'], 'uncertain')
                self.assertEqual(len(self.calls), 1)
            finally:
                gate.set()
                self.assertTrue(ended.wait(0.5))


if __name__ == '__main__':
    unittest.main()
