"""
EpsInc - Locust Load Testing Suite
Simulates 1000 active players (WASD movement, aiming, shooting) and 500 spectators via WebSockets.
"""
import json
import math
import random
import time
import websocket
import gevent
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
        self.receiver = None
        self.ping_started = None
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
            if resp.get("type") != "init_success":
                raise RuntimeError(f"Join rejected: {resp.get('message', resp.get('type'))}")
            if resp.get("type") == "init_success":
                self.player_id = resp.get("player_id")
                self.connected = True
                self.receiver = gevent.spawn(self._receive_messages)
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

    def _receive_messages(self):
        while self.connected:
            try:
                message = json.loads(self.ws.recv())
                if message.get("type") == "pong" and self.ping_started is not None:
                    elapsed = (time.perf_counter() - self.ping_started) * 1000
                    self.ping_started = None
                    events.request.fire(
                        request_type="WebSocket",
                        name="Player_Ping_RTT",
                        response_time=elapsed,
                        response_length=len(json.dumps(message)),
                        context=None,
                        exception=None
                    )
            except Exception as error:
                events.request.fire(
                    request_type="WebSocket", name="Player_Disconnected",
                    response_time=0, response_length=0, context=None, exception=error
                )
                self.connected = False
                break

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
        if self.ping_started is not None:
            return
        t0 = time.perf_counter()
        try:
            self.ping_started = t0
            self.ws.send(json.dumps({"type": "ping", "t": time.time()}))
        except Exception as e:
            self.connected = False
            events.request.fire(
                request_type="WebSocket",
                name="Player_Ping_RTT",
                response_time=0,
                response_length=0,
                context=None,
                exception=e
            )

    def on_stop(self):
        self.connected = False
        if self.receiver:
            self.receiver.kill(block=False)
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
            if resp.get("type") != "init_success":
                raise RuntimeError(f"Join rejected: {resp.get('message', resp.get('type'))}")
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
