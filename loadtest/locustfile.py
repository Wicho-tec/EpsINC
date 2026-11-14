"""
EpsInc - Locust Load Testing Suite
Simulates 1000 active players (WASD movement, aiming, shooting) and 500 spectators via WebSockets.
"""
import json
import math
import random
import time
import websocket
from locust import User, task, between, events

class EpsIncPlayerUser(User):
    """Simulates an active playing baby bottle (WASD, aiming, shooting)."""
    wait_time = between(0.08, 0.12) # ~10 input updates per second

    def on_start(self):
        self.host_ws = self.environment.host.replace("http://", "ws://").replace("https://", "wss://")
        self.room_id = f"arena-{random.randint(1, 5)}"
        self.ws_url = f"{self.host_ws}/ws/{self.room_id}"
        self.player_id = None
        self.ws = None
        self.connected = False
        self.angle = random.uniform(0, 2 * math.pi)
        started = time.perf_counter()

        try:
            self.ws = websocket.create_connection(self.ws_url, timeout=5)
            # Handshake join
            self.ws.send(json.dumps({
                "name": f"Locust_{random.randint(1000, 9999)}",
                "color": "#00D2D3",
                "is_spectator": False
            }))
            resp = json.loads(self.ws.recv())
            if resp.get("type") == "init_success":
                self.player_id = resp.get("player_id")
                self.connected = True
                events.request.fire(
                    request_type="WebSocket",
                    name="Player_Connect",
                    response_time=(time.perf_counter() - started) * 1000,
                    response_length=len(json.dumps(resp)),
                    context=None,
                    exception=None
                )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="Player_Connect",
                response_time=0,
                response_length=0,
                context=None,
                exception=e
            )

    @task(8)
    def send_gameplay_input(self):
        if not self.connected or not self.ws:
            return
        t0 = time.perf_counter()
        try:
            # Simulate movement
            mx = random.choice([-1.0, 0.0, 1.0])
            my = random.choice([-1.0, 0.0, 1.0])
            self.angle += random.uniform(-0.2, 0.2)
            should_shoot = random.random() < 0.15 # 15% shoot probability per tick

            payload = {
                "type": "input",
                "move_x": mx,
                "move_y": my,
                "angle": self.angle,
                "shoot": should_shoot
            }
            self.ws.send(json.dumps(payload))
            elapsed = (time.perf_counter() - t0) * 1000

            events.request.fire(
                request_type="WebSocket",
                name="Player_Input_Move_Shoot",
                response_time=elapsed,
                response_length=len(json.dumps(payload)),
                context=None,
                exception=None
            )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="Player_Input_Move_Shoot",
                response_time=0,
                response_length=0,
                context=None,
                exception=e
            )

    @task(1)
    def ping_latency(self):
        if not self.connected or not self.ws:
            return
        t0 = time.perf_counter()
        try:
            sent_at = time.time()
            self.ws.send(json.dumps({"type": "ping", "t": sent_at}))
            msg = json.loads(self.ws.recv())
            rtt = (time.perf_counter() - t0) * 1000

            events.request.fire(
                request_type="WebSocket",
                name="Player_Ping_RTT",
                response_time=rtt,
                response_length=len(json.dumps(msg)),
                context=None,
                exception=None
            )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="Player_Ping_RTT",
                response_time=0,
                response_length=0,
                context=None,
                exception=e
            )

    def on_stop(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass


class EpsIncSpectatorUser(User):
    """Simulates passive spectators consuming match broadcasts."""
    wait_time = between(0.03, 0.05)

    def on_start(self):
        self.host_ws = self.environment.host.replace("http://", "ws://").replace("https://", "wss://")
        self.room_id = f"arena-{random.randint(1, 5)}"
        self.ws_url = f"{self.host_ws}/ws/{self.room_id}"
        self.ws = None
        self.connected = False
        started = time.perf_counter()

        try:
            self.ws = websocket.create_connection(self.ws_url, timeout=5)
            self.ws.send(json.dumps({
                "name": f"Spectator_{random.randint(100, 999)}",
                "is_spectator": True
            }))
            resp = json.loads(self.ws.recv())
            self.connected = True
            events.request.fire(
                request_type="WebSocket",
                name="Spectator_Connect",
                response_time=(time.perf_counter() - started) * 1000,
                response_length=len(json.dumps(resp)),
                context=None,
                exception=None
            )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="Spectator_Connect",
                response_time=0,
                response_length=0,
                context=None,
                exception=e
            )

    @task
    def receive_state_broadcast(self):
        if not self.connected or not self.ws:
            return
        t0 = time.perf_counter()
        try:
            raw = self.ws.recv()
            elapsed = (time.perf_counter() - t0) * 1000
            events.request.fire(
                request_type="WebSocket",
                name="Spectator_Receive_Snapshot",
                response_time=elapsed,
                response_length=len(raw),
                context=None,
                exception=None
            )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="Spectator_Receive_Snapshot",
                response_time=0,
                response_length=0,
                context=None,
                exception=e
            )

    def on_stop(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
