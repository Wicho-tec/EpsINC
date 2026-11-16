import json
import unittest
from unittest.mock import Mock, patch
import time

from loadtest.locustfile import EpsIncPlayerUser


class PlayerReceiverTests(unittest.TestCase):
    def test_only_pong_counts_as_round_trip_and_disconnect_is_recorded(self):
        user = object.__new__(EpsIncPlayerUser)
        user.connected = True
        user.ping_started = time.perf_counter()
        user.ws = Mock()
        user.ws.recv.side_effect = [json.dumps({"type": "snapshot"}),
                                    json.dumps({"type": "pong"}), OSError("closed")]
        with patch("loadtest.locustfile.events.request.fire") as record:
            user._receive_messages()
        self.assertEqual([call.kwargs["name"] for call in record.call_args_list],
                         ["Player_Ping_RTT", "Player_Disconnected"])
        self.assertFalse(user.connected)
        self.assertIsNone(user.ping_started)
        self.assertIsInstance(record.call_args.kwargs["exception"], OSError)


if __name__ == "__main__":
    unittest.main()
