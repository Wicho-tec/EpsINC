"""
EpsInc - Data Models
Pydantic and dataclass models for game state, players, projectiles, and rooms.
"""
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field
import time
import uuid

class PowerUpType:
    SPEED_BOOST = "SPEED_BOOST"
    MEGA_BEAM = "MEGA_BEAM"
    RAPID_BURST = "RAPID_BURST"
    SHIELD = "SHIELD"
    MULTI_BOUNCE = "MULTI_BOUNCE"

class PlayerState(BaseModel):
    id: str
    name: str
    color: str
    x: float
    y: float
    angle: float = 0.0          # Angle facing (aim direction of nipple)
    body_angle: float = 0.0     # Movement facing
    vx: float = 0.0
    vy: float = 0.0
    alive: bool = True
    score: int = 0
    kills: int = 0
    deaths: int = 0
    streak: int = 0             # Consecutive kills without dying
    shield: bool = False
    shield_timer: float = 0.0
    speed_boost_timer: float = 0.0
    multi_bounce_timer: float = 0.0
    beam_charge_timer: float = 0.0
    beam_firing: bool = False
    beam_start_x: float = 0.0
    beam_start_y: float = 0.0
    beam_end_x: float = 0.0
    beam_end_y: float = 0.0
    rapid_burst_charges: int = 0
    cooldown: float = 0.0
    is_bot: bool = False
    is_spectator: bool = False
    active_power: Optional[str] = None
    respawn_timer: float = 0.0

class BulletState(BaseModel):
    id: str
    owner_id: str
    x: float
    y: float
    vx: float
    vy: float
    radius: float = 6.0
    bounces_left: int = 4
    max_bounces: int = 4
    created_at: float
    lifespan: float = 5.0       # Exactly 5 seconds
    is_beam: bool = False
    color: str = "#FFE600"

class PowerUpItem(BaseModel):
    id: str
    type: str                   # PowerUpType
    x: float
    y: float
    active: bool = True
    respawn_at: float = 0.0

class WallRect(BaseModel):
    x: float
    y: float
    w: float
    h: float
    color: str = "#E52521"      # LEGO brick colors (red, blue, yellow, green, orange)
    brick_type: str = "rect"

class MapDefinition(BaseModel):
    id: str
    name: str
    width: int
    height: int
    theme: str
    background_color: str
    walls: List[WallRect]
    spawn_points: List[Tuple[float, float]]
    powerup_spawns: List[Tuple[float, float]]

class RoomSummary(BaseModel):
    id: str
    name: str
    map_id: str
    map_name: str
    player_count: int
    max_players: int = 20
    spectator_count: int
    bots_enabled: bool
    status: str                 # "waiting", "in_progress", "ended"
    winner: Optional[str] = None
