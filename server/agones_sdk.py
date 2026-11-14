"""Minimal Agones lifecycle client over its local REST sidecar."""
import os
import threading
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


class AgonesLifecycle:
    def __init__(self):
        self.port = os.getenv("AGONES_SDK_HTTP_PORT")
        self.stop_event = threading.Event()
        self.health_thread = None

    def _post(self, path):
        request = Request(
            f"http://127.0.0.1:{self.port}/{path}",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2):
            return

    def start(self):
        if not self.port:
            return
        for attempt in range(30):
            try:
                self._post("ready")
                break
            except (OSError, URLError):
                if attempt == 29:
                    raise
                time.sleep(1)
        self.health_thread = threading.Thread(target=self._send_health, daemon=True)
        self.health_thread.start()

    def _send_health(self):
        while not self.stop_event.is_set():
            try:
                self._post("health")
            except (OSError, URLError):
                pass
            self.stop_event.wait(2)

    def stop(self):
        if not self.port:
            return
        self.stop_event.set()
        try:
            self._post("shutdown")
        except (OSError, URLError):
            pass


agones = AgonesLifecycle()
