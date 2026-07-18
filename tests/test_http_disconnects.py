import unittest
from unittest.mock import Mock

from server import Handler


class HttpDisconnectTest(unittest.TestCase):
    def test_json_response_treats_client_disconnect_as_transport_completion(self):
        handler = object.__new__(Handler)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.wfile.write.side_effect = BrokenPipeError(32, "client disconnected")
        handler.close_connection = False

        sent = handler.send_json({"ok": True})

        self.assertFalse(sent)
        self.assertTrue(handler.close_connection)


if __name__ == "__main__":
    unittest.main()
