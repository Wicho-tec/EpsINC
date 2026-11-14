import os
import unittest
from unittest.mock import patch

from server.agones_sdk import AgonesLifecycle


class AgonesLifecycleTests(unittest.TestCase):
    def test_local_mode_does_not_contact_sidecar(self):
        with patch.dict(os.environ, {}, clear=True):
            sdk = AgonesLifecycle()
            with patch.object(sdk, "_post") as post:
                sdk.start()
                sdk.stop()
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
