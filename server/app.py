"""
EpsInc - FastAPI Web & WebSocket Server
Serves static Phaser 3 client, REST APIs, Prometheus metrics, and manages real-time WebSocket sessions.
"""
import asyncio
import json
import os
import time
import uuid
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

from server.models import MapDefinition, RoomSummary
from server.maps import ALL_MAPS, get_map
from server.game_engine import GameManager, GameRoom
from server.agones_sdk import agones

app = FastAPI(title="EpsInc Game Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics
PROM_CCU = Gauge("epsinc_connected_players", "Number of connected players", ["room_id", "type"])
PROM_ACTIVE_ROOMS = Gauge("epsinc_active_rooms", "Number of active game rooms")
PROM_TOTAL_KILLS = Counter("epsinc_total_kills", "Total kills executed in game")
PROM_TICK_LATENCY = Histogram(
    "epsinc_tick_duration_seconds",
    "Time spent in game physics tick calculation",
    buckets=[0.001, 0.002, 0.005, 0.010, 0.020, 0.033, 0.050, 0.100]
)
PROM_WS_MESSAGES = Counter("epsinc_ws_messages_total", "Total WebSocket messages received", ["type"])

game_manager = GameManager()
BASE_DIR = Path(__file__).resolve().parent.parent
CLIENT_DIR = BASE_DIR / "client"

# Mount static files
app.mount("/static", StaticFiles(directory=str(CLIENT_DIR)), name="static")

@app.on_event("startup")
async def notify_agones_ready():
    await asyncio.to_thread(agones.start)

@app.on_event("shutdown")
async def notify_agones_shutdown():
    agones.stop()

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = CLIENT_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>EpsInc Client building...</h1>")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))

@app.get("/health")
async def health_check():
    """Kubernetes & Agones health probe endpoint."""
    return {
        "status": "healthy",
        "service": "EpsInc",
        "timestamp": time.time(),
        "active_rooms": len(game_manager.rooms)
    }

@app.get("/metrics")
async def metrics():
    """Prometheus scraping endpoint."""
    # Update current gauges
    PROM_ACTIVE_ROOMS.set(len(game_manager.rooms))
    for r_id, room in game_manager.rooms.items():
        humans = sum(1 for p in room.players.values() if not p.is_bot and not p.is_spectator)
        bots = sum(1 for p in room.players.values() if p.is_bot)
        spectators = len(room.spectators)
        PROM_CCU.labels(room_id=r_id, type="human").set(humans)
        PROM_CCU.labels(room_id=r_id, type="bot").set(bots)
        PROM_CCU.labels(room_id=r_id, type="spectator").set(spectators)

    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/maps")
async def list_maps():
    return [
        {
            "id": m.id,
            "name": m.name,
            "theme": m.theme,
            "width": m.width,
            "height": m.height,
            "background_color": m.background_color,
            "wall_count": len(m.walls),
            "powerup_count": len(m.powerup_spawns)
        }
        for m in ALL_MAPS.values()
    ]

@app.get("/api/maps/{map_id}")
async def get_map_details(map_id: str):
    m = get_map(map_id)
    return m.dict()

@app.get("/api/rooms")
async def list_rooms():
    return [summary.dict() for summary in game_manager.list_rooms()]

@app.post("/api/rooms")
async def create_room(payload: Dict[str, Any]):
    room_name = payload.get("name", "Arena Personalizada")
    map_id = payload.get("map_id", "ciudad_bloques")
    max_players = min(20, max(2, int(payload.get("max_players", 20))))
    bots_enabled = bool(payload.get("bots_enabled", True))
    target_bots = int(payload.get("target_bots", 5))

    room_id = f"room-{uuid.uuid4().hex[:6]}"
    room = game_manager.create_room(
        room_id=room_id,
        name=room_name,
        map_id=map_id,
        max_players=max_players,
        bots_enabled=bots_enabled,
        target_bots=target_bots
    )
    if os.environ.get("EPSINC_TESTING") != "1":
        room.task = asyncio.create_task(run_room_loop(room))
    return room.get_summary().dict()


async def run_room_loop(room: GameRoom):
    """30 FPS Authoritative Simulation Loop for a single room."""
    TICK_RATE = 30.0
    DT = 1.0 / TICK_RATE
    room.is_running = True

    try:
        while room.is_running:
            t0 = time.perf_counter()
            try:
                with PROM_TICK_LATENCY.time():
                    room.update(DT)

                # Broadcast state concurrently to all active connections
                if room.connections:
                    snapshot = room.get_snapshot()
                    msg = json.dumps(snapshot, separators=(',', ':'))
                    
                    # Check kills event to increment Prometheus
                    for evt in snapshot.get("events", []):
                        if evt.get("type") == "player_killed":
                            PROM_TOTAL_KILLS.inc()

                    items = list(room.connections.items())
                    if items:
                        async def _safe_send(pid, ws):
                            try:
                                await ws.send_text(msg)
                                return None
                            except Exception:
                                return pid

                        results = await asyncio.gather(*[_safe_send(pid, ws) for pid, ws in items], return_exceptions=True)
                        for res in results:
                            if isinstance(res, str):
                                room.remove_player(res)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"Error in room {room.room_id} loop: {e}")

            elapsed = time.perf_counter() - t0
            sleep_time = max(0.001, DT - elapsed)
            await asyncio.sleep(sleep_time)
    except asyncio.CancelledError:
        room.is_running = False


@app.on_event("startup")
async def startup_event():
    # Only auto-start room loops if not disabled (e.g. during testing)
    if os.environ.get("EPSINC_TESTING") == "1":
        return
    for room in game_manager.rooms.values():
        room.task = asyncio.create_task(run_room_loop(room))

@app.on_event("shutdown")
async def shutdown_event():
    for room in game_manager.rooms.values():
        room.is_running = False
        if room.task:
            room.task.cancel()


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    room = game_manager.get_room(room_id)
    if not room:
        await websocket.send_json({"type": "error", "message": "Sala no encontrada"})
        await websocket.close()
        return

    player_id = f"p_{uuid.uuid4().hex[:8]}"
    player_name = "Biberon"
    reconnect_token = None
    is_spectator = False

    try:
        # 1. Handshake message
        init_data = await websocket.receive_json()
        PROM_WS_MESSAGES.labels(type="join").inc()
        
        req_token = init_data.get("reconnect_token")
        if req_token and req_token in room.reconnect_tokens:
            # Reconnect existing player
            player_id = room.reconnect_tokens[req_token]
            if player_id in room.players:
                player = room.players[player_id]
                player_name = player.name
                reconnect_token = req_token
            else:
                player, reconnect_token = room.add_player(
                    player_id=player_id,
                    name=init_data.get("name", "Biberon"),
                    is_spectator=init_data.get("is_spectator", False),
                    custom_color=init_data.get("color")
                )
        else:
            is_spectator = bool(init_data.get("is_spectator", False))
            player_name = init_data.get("name", "Biberon")[:20]
            player, reconnect_token = room.add_player(
                player_id=player_id,
                name=player_name,
                is_spectator=is_spectator,
                custom_color=init_data.get("color")
            )

        room.connections[player_id] = websocket

        # Send welcome init response with map data
        await websocket.send_json({
            "type": "init_success",
            "player_id": player_id,
            "reconnect_token": reconnect_token,
            "is_spectator": is_spectator,
            "room_id": room_id,
            "room_name": room.name,
            "map": room.map_def.dict()
        })

        # 2. Continuous message loop
        while True:
            data = await websocket.receive_json()
            mtype = data.get("type")

            if mtype == "input":
                PROM_WS_MESSAGES.labels(type="input").inc()
                room.handle_input(player_id, data)

            elif mtype == "toggle_bots":
                # Host sets bot properties
                room.bots_enabled = bool(data.get("enabled", True))
                if "target_bots" in data:
                    room.target_bots = int(data["target_bots"])
                room._sync_bots()

            elif mtype == "restart_round":
                room.restart_match()

            elif mtype == "ping":
                # Return pong for p99 latency measurement
                client_t = data.get("t", 0.0)
                await websocket.send_json({
                    "type": "pong",
                    "client_t": client_t,
                    "server_t": time.time()
                })

    except WebSocketDisconnect:
        room.remove_player(player_id)
    except Exception as e:
        print(f"WS error for {player_id}: {e}")
        room.remove_player(player_id)
