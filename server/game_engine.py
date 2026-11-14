"""
EpsInc - Server Authoritative Game Engine (Ultra-Lightweight 1-Life Elimination)
Rules:
- 1 Life per player (Battle Royale / Last Man Standing).
- No respawns during the round.
- When killed by an enemy, camera spectates the killer.
- When killed by own bullet, camera spectates a random living player.
- When only 1 survivor remains: EPSWIN for the winner, EPSLOSE for eliminated players.
- O(1) Spatial Hash Grid for collision detection.
"""
import asyncio
import copy
import math
import random
import time
import uuid
from typing import Dict, List, Optional, Set, Tuple, Any

from server.models import (
    PlayerState, BulletState, PowerUpItem, PowerUpType,
    WallRect, MapDefinition, RoomSummary
)
from server.maps import ALL_MAPS, get_map
from server.bot_ai import BotAI

PLAYER_RADIUS = 24.0
BULLET_RADIUS = 6.0
BASE_PLAYER_SPEED = 220.0
BULLET_SPEED = 560.0

PLAYER_COLORS = [
    "#00D2D3", "#FF6B6B", "#FECA57", "#1DD1A1", "#54A0FF",
    "#9B30FF", "#FF9FF3", "#FF9F43", "#48DBFB", "#10AC84",
    "#EE5253", "#341f97", "#0abde3", "#ff7979", "#badc58",
    "#686de0", "#30336b", "#f6e58d", "#e056fd", "#22a6b3"
]

BOT_NAMES = [
    "BabyTerminator", "ChupetePro", "TetinaVeloz", "LegoKing", "BiberonBot",
    "PoderosoBebe", "BouncingBaby", "AlphaBottle", "RoboNipple", "BrickMaster",
    "MegaBiberon", "DrChupon", "NanoBottle", "PixelBiberon", "LegoSniper",
    "BottleGamer", "CyberBaby", "TurboChupon", "SuperTetina", "OmegaBottle"
]

class SpatialWallGrid:
    """Fast spatial partitioner for O(1) wall collision queries."""
    __slots__ = ('cell_size', 'cols', 'rows', 'grid')

    def __init__(self, width: int, height: int, cell_size: int = 180):
        self.cell_size = cell_size
        self.cols = max(1, (width // cell_size) + 1)
        self.rows = max(1, (height // cell_size) + 1)
        self.grid: Dict[Tuple[int, int], List[WallRect]] = {}

    def build(self, walls: List[WallRect]):
        self.grid.clear()
        cs = self.cell_size
        for w in walls:
            min_c = max(0, int(w.x // cs))
            max_c = min(self.cols - 1, int((w.x + w.w) // cs))
            min_r = max(0, int(w.y // cs))
            max_r = min(self.rows - 1, int((w.y + w.h) // cs))
            for c in range(min_c, max_c + 1):
                for r in range(min_r, max_r + 1):
                    key = (c, r)
                    if key not in self.grid:
                        self.grid[key] = []
                    self.grid[key].append(w)

    def get_candidate_walls(self, x: float, y: float, radius: float) -> List[WallRect]:
        cs = self.cell_size
        min_c = max(0, int((x - radius) // cs))
        max_c = min(self.cols - 1, int((x + radius) // cs))
        min_r = max(0, int((y - radius) // cs))
        max_r = min(self.rows - 1, int((y + radius) // cs))

        if min_c == max_c and min_r == max_r:
            return self.grid.get((min_c, min_r), [])

        res: List[WallRect] = []
        seen = set()
        for c in range(min_c, max_c + 1):
            for r in range(min_r, max_r + 1):
                cell = self.grid.get((c, r))
                if cell:
                    for w in cell:
                        wid = id(w)
                        if wid not in seen:
                            seen.add(wid)
                            res.append(w)
        return res


class GameRoom:
    def __init__(self, room_id: str, name: str, map_id: str = "ciudad_bloques",
                 max_players: int = 20, bots_enabled: bool = True, target_bots: int = 5,
                 max_score: int = 15):
        self.room_id = room_id
        self.name = name
        self.map_def = copy.deepcopy(get_map(map_id))
        self.max_players = min(20, max_players)
        self.bots_enabled = bots_enabled
        self.target_bots = target_bots
        self.max_score = max_score
        
        # Spatial partitioning
        self.spatial_grid = SpatialWallGrid(self.map_def.width, self.map_def.height, cell_size=180)
        self.spatial_grid.build(self.map_def.walls)
        self._last_walls_id = id(self.map_def.walls)
        self._last_wall_count = len(self.map_def.walls)

        # State collections
        self.players: Dict[str, PlayerState] = {}
        self.spectators: Set[str] = set()
        self.bullets: Dict[str, BulletState] = {}
        self.powerups: Dict[str, PowerUpItem] = {}
        self.bots: Dict[str, BotAI] = {}
        self.connections: Dict[str, Any] = {}
        
        # Room status
        self.status = "waiting" # "waiting", "in_progress", "ended"
        self.winner: Optional[str] = None
        self.created_at = time.time()
        self.events_queue: List[Dict[str, Any]] = []
        
        # Cached snapshot data & dirty flags
        self._cached_leaderboard: List[Dict[str, Any]] = []
        self._leaderboard_dirty = True
        
        self._init_powerups()
        self.reconnect_tokens: Dict[str, str] = {}
        
        self.task: Optional[asyncio.Task] = None
        self.is_running = False

    def _init_powerups(self):
        power_types = [
            PowerUpType.SPEED_BOOST,
            PowerUpType.MEGA_BEAM,
            PowerUpType.RAPID_BURST,
            PowerUpType.SHIELD,
            PowerUpType.MULTI_BOUNCE
        ]
        now = time.time()
        for idx, (px, py) in enumerate(self.map_def.powerup_spawns):
            ptype = power_types[idx % len(power_types)]
            pu_id = f"pw_{idx}_{int(now)}"
            self.powerups[pu_id] = PowerUpItem(
                id=pu_id,
                type=ptype,
                x=px,
                y=py,
                active=True,
                respawn_at=0.0
            )

    def get_summary(self) -> RoomSummary:
        active_human = sum(1 for p in self.players.values() if not p.is_bot and not p.is_spectator)
        bot_count = sum(1 for p in self.players.values() if p.is_bot)
        return RoomSummary(
            id=self.room_id,
            name=self.name,
            map_id=self.map_def.id,
            map_name=self.map_def.name,
            player_count=active_human + bot_count,
            max_players=self.max_players,
            spectator_count=len(self.spectators),
            bots_enabled=self.bots_enabled,
            status=self.status,
            winner=self.winner
        )

    def get_available_spawn(self) -> Tuple[float, float]:
        if not self.map_def.spawn_points:
            return (self.map_def.width / 2, self.map_def.height / 2)
        living_coords = [(p.x, p.y) for p in self.players.values() if p.alive and not p.is_spectator]
        if not living_coords:
            return random.choice(self.map_def.spawn_points)

        best_spawn = random.choice(self.map_def.spawn_points)
        max_min_dist = -1.0
        for sx, sy in self.map_def.spawn_points:
            min_dist = min(math.hypot(px - sx, py - sy) for px, py in living_coords)
            if min_dist > max_min_dist:
                max_min_dist = min_dist
                best_spawn = (sx, sy)
        return best_spawn

    def add_player(self, player_id: str, name: str, is_spectator: bool = False,
                   custom_color: Optional[str] = None) -> Tuple[PlayerState, str]:
        self._leaderboard_dirty = True
        token = str(uuid.uuid4())
        self.reconnect_tokens[token] = player_id

        if is_spectator:
            self.spectators.add(player_id)
            player = PlayerState(
                id=player_id,
                name=name,
                color="#FFFFFF",
                x=self.map_def.width / 2,
                y=self.map_def.height / 2,
                is_spectator=True,
                alive=False
            )
            self.players[player_id] = player
            return player, token

        # Normal player joining fresh match
        color = custom_color or PLAYER_COLORS[len(self.players) % len(PLAYER_COLORS)]
        sx, sy = self.get_available_spawn()
        player = PlayerState(
            id=player_id,
            name=name,
            color=color,
            x=sx,
            y=sy,
            angle=0.0,
            is_spectator=False,
            alive=True
        )
        self.players[player_id] = player
        
        if self.status == "waiting":
            self.status = "in_progress"

        self.events_queue.append({
            "type": "player_joined",
            "player_id": player_id,
            "name": name,
            "color": color,
            "is_spectator": False
        })
        
        self._sync_bots()
        return player, token

    def restart_match(self):
        """Restarts a fresh 1-life elimination round."""
        self.status = "in_progress"
        self.winner = None
        self.bullets.clear()
        self._leaderboard_dirty = True
        
        # Reset all players and bots to 1 life
        for p in self.players.values():
            if not p.is_spectator:
                sx, sy = self.get_available_spawn()
                p.x = sx
                p.y = sy
                p.alive = True
                p.shield = False
                p.speed_boost_timer = 0
                p.multi_bounce_timer = 0
                p.beam_charge_timer = 0
                p.rapid_burst_charges = 0
                p.active_power = None
                p.cooldown = 0
                p.streak = 0

        self.events_queue.append({
            "type": "match_restarted"
        })

    def remove_player(self, player_id: str):
        self._leaderboard_dirty = True
        if player_id in self.spectators:
            self.spectators.discard(player_id)
        if player_id in self.players:
            p = self.players.pop(player_id)
            if player_id in self.bots:
                del self.bots[player_id]
            self.events_queue.append({
                "type": "player_left",
                "player_id": player_id,
                "name": p.name
            })
        if player_id in self.connections:
            del self.connections[player_id]
        
        self._sync_bots()
        self._check_last_man_standing()

    def _sync_bots(self):
        if not self.bots_enabled:
            bot_ids = [pid for pid, p in self.players.items() if p.is_bot]
            for bid in bot_ids:
                if bid in self.players:
                    del self.players[bid]
                if bid in self.bots:
                    del self.bots[bid]
            self._leaderboard_dirty = True
            return

        humans = sum(1 for p in self.players.values() if not p.is_bot and not p.is_spectator)
        current_bots = sum(1 for p in self.players.values() if p.is_bot)
        desired_bots = max(0, min(self.target_bots, self.max_players - humans))

        while current_bots < desired_bots:
            bot_id = f"bot_{uuid.uuid4().hex[:6]}"
            name = BOT_NAMES[len(self.bots) % len(BOT_NAMES)]
            color = PLAYER_COLORS[(humans + current_bots) % len(PLAYER_COLORS)]
            sx, sy = self.get_available_spawn()
            bot_player = PlayerState(
                id=bot_id,
                name=f"[BOT] {name}",
                color=color,
                x=sx,
                y=sy,
                is_bot=True,
                alive=True
            )
            self.players[bot_id] = bot_player
            self.bots[bot_id] = BotAI(bot_id, name, color)
            current_bots += 1
            self._leaderboard_dirty = True

        while current_bots > desired_bots:
            for bid in list(self.bots.keys()):
                if bid in self.players:
                    del self.players[bid]
                del self.bots[bid]
                current_bots -= 1
                self._leaderboard_dirty = True
                if current_bots <= desired_bots:
                    break

    def handle_input(self, player_id: str, input_data: Dict[str, Any]):
        player = self.players.get(player_id)
        if not player or not player.alive or player.is_spectator:
            return

        mx = float(input_data.get("move_x", 0.0))
        my = float(input_data.get("move_y", 0.0))
        norm_sq = mx * mx + my * my
        if norm_sq > 1.0:
            inv = 1.0 / math.sqrt(norm_sq)
            mx *= inv
            my *= inv
        player.vx = mx
        player.vy = my
        
        if "angle" in input_data:
            player.angle = float(input_data["angle"])
            
        if input_data.get("shoot", False):
            self.trigger_shoot(player)

    def trigger_shoot(self, player: PlayerState):
        now = time.time()
        if not player.alive or player.cooldown > 0:
            return

        tip_offset = 32.0
        bx = player.x + math.cos(player.angle) * tip_offset
        by = player.y + math.sin(player.angle) * tip_offset
        max_bounces = 12 if player.multi_bounce_timer > 0 else 4

        if player.rapid_burst_charges > 0:
            player.rapid_burst_charges -= 1
            for spread in (-0.18, -0.06, 0.06, 0.18):
                ang = player.angle + spread
                b_id = f"b_{uuid.uuid4().hex[:8]}"
                bullet = BulletState(
                    id=b_id,
                    owner_id=player.id,
                    x=bx,
                    y=by,
                    vx=math.cos(ang) * BULLET_SPEED,
                    vy=math.sin(ang) * BULLET_SPEED,
                    bounces_left=max_bounces,
                    max_bounces=max_bounces,
                    created_at=now,
                    lifespan=5.0,
                    color="#FF9F43"
                )
                self.bullets[b_id] = bullet
            player.cooldown = 0.28
            self.events_queue.append({
                "type": "shoot_sound",
                "x": bx,
                "y": by,
                "rapid": True
            })
            return

        if player.active_power == PowerUpType.MEGA_BEAM and player.beam_charge_timer <= 0:
            player.beam_charge_timer = 2.0
            player.cooldown = 2.6
            self.events_queue.append({
                "type": "beam_charging",
                "player_id": player.id,
                "x": player.x,
                "y": player.y,
                "angle": player.angle,
                "duration": 2.0
            })
            return

        player.cooldown = 0.35
        b_id = f"b_{uuid.uuid4().hex[:8]}"
        bullet = BulletState(
            id=b_id,
            owner_id=player.id,
            x=bx,
            y=by,
            vx=math.cos(player.angle) * BULLET_SPEED,
            vy=math.sin(player.angle) * BULLET_SPEED,
            bounces_left=max_bounces,
            max_bounces=max_bounces,
            created_at=now,
            lifespan=5.0,
            color=player.color
        )
        self.bullets[b_id] = bullet
        self.events_queue.append({
            "type": "shoot_sound",
            "x": bx,
            "y": by,
            "rapid": False
        })

    def fire_mega_beam(self, player: PlayerState):
        player.active_power = None
        angle = player.angle
        start_x = player.x + math.cos(angle) * 32.0
        start_y = player.y + math.sin(angle) * 32.0
        beam_len = 2500.0
        end_x = start_x + math.cos(angle) * beam_len
        end_y = start_y + math.sin(angle) * beam_len

        self.events_queue.append({
            "type": "mega_beam_fired",
            "player_id": player.id,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y
        })

        for victim_id, victim in list(self.players.items()):
            if victim_id == player.id or not victim.alive or victim.is_spectator:
                continue
            dist_to_beam = self._point_to_line_dist(victim.x, victim.y, start_x, start_y, end_x, end_y)
            if dist_to_beam <= PLAYER_RADIUS + 16.0:
                self.kill_player(victim, player.id, was_beam=True)

    def _point_to_line_dist(self, px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
        dx = x2 - x1
        dy = y2 - y1
        l2 = dx * dx + dy * dy
        if l2 == 0:
            return math.hypot(px - x1, py - y1)
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    def kill_player(self, victim: PlayerState, killer_id: Optional[str], was_beam: bool = False):
        if victim.shield and not was_beam:
            victim.shield = False
            victim.shield_timer = 0.0
            self.events_queue.append({
                "type": "shield_broken",
                "player_id": victim.id
            })
            return

        # 1-LIFE ELIMINATION: The player is permanently dead this round!
        victim.alive = False
        victim.deaths += 1
        victim.respawn_timer = 0.0
        victim.streak = 0
        victim.active_power = None
        self._leaderboard_dirty = True

        killer = self.players.get(killer_id) if killer_id else None
        streak_count = 0
        if killer and killer.id != victim.id:
            killer.score += 1
            killer.kills += 1
            killer.streak += 1
            streak_count = killer.streak
        else:
            if killer:
                killer.streak = 0

        # Determine who the victim should spectate now:
        # If killed by someone else and that killer is alive -> spectate killer!
        # If killed by self/bounced bullet or killer is dead -> spectate random living player!
        living_others = [p.id for p in self.players.values() if p.alive and not p.is_spectator and p.id != victim.id]
        spectate_target_id = None
        if killer and killer.id != victim.id and killer.alive:
            spectate_target_id = killer.id
        elif living_others:
            spectate_target_id = random.choice(living_others)

        self.events_queue.append({
            "type": "player_killed",
            "victim_id": victim.id,
            "victim_name": victim.name,
            "killer_id": killer.id if killer else None,
            "killer_name": killer.name if killer else "Rebote Propio",
            "spectate_target_id": spectate_target_id,
            "streak": streak_count,
            "x": victim.x,
            "y": victim.y
        })

        # Check Last Man Standing
        self._check_last_man_standing()

    def _check_last_man_standing(self):
        """Verifies if only 1 living combatant remains to declare EPSWIN / EPSLOSE."""
        if self.status == "ended":
            return

        combatants = [p for p in self.players.values() if not p.is_spectator]
        living = [p for p in combatants if p.alive]

        # If there were players and now only 1 (or 0) remains:
        if len(combatants) >= 2 and len(living) == 1:
            winner = living[0]
            self.status = "ended"
            self.winner = winner.name
            self.events_queue.append({
                "type": "match_won",
                "winner_id": winner.id,
                "winner_name": winner.name,
                "score": winner.score
            })
        elif len(combatants) >= 1 and len(living) == 0:
            # Everyone eliminated
            self.status = "ended"
            self.winner = "Nadie (Empate)"
            self.events_queue.append({
                "type": "match_won",
                "winner_id": None,
                "winner_name": "Empate",
                "score": 0
            })

    def update(self, dt: float):
        now = time.time()

        # 1. Update Bots
        if self.bots_enabled and self.status == "in_progress":
            for bot_id, bot in self.bots.items():
                p = self.players.get(bot_id)
                if not p or not p.alive:
                    continue
                mx, my, ang, shoot = bot.update(
                    dt, p, self.players, self.map_def.walls,
                    list(self.powerups.values()), self.map_def.width, self.map_def.height
                )
                p.vx = mx
                p.vy = my
                p.angle = ang
                if shoot:
                    self.trigger_shoot(p)

        # 2. Update Living Players
        for p in self.players.values():
            if p.is_spectator or not p.alive:
                continue

            if p.cooldown > 0:
                p.cooldown -= dt
            
            if p.beam_charge_timer > 0:
                p.beam_charge_timer -= dt
                if p.beam_charge_timer <= 0:
                    self.fire_mega_beam(p)

            speed = BASE_PLAYER_SPEED
            if p.speed_boost_timer > 0:
                p.speed_boost_timer -= dt
                speed *= 1.6

            if p.shield_timer > 0:
                p.shield_timer -= dt
                if p.shield_timer <= 0:
                    p.shield = False

            if p.multi_bounce_timer > 0:
                p.multi_bounce_timer -= dt

            if p.vx != 0 or p.vy != 0:
                dx = p.vx * speed * dt
                dy = p.vy * speed * dt
                self._move_circle_against_walls(p, dx, dy)

            # Check powerup pickups
            for pu in self.powerups.values():
                if pu.active:
                    d_sq = (p.x - pu.x) ** 2 + (p.y - pu.y) ** 2
                    if d_sq <= (PLAYER_RADIUS + 18.0) ** 2:
                        self._apply_powerup(p, pu)

        # 3. Update Powerup Respawns
        for pu in self.powerups.values():
            if not pu.active and now >= pu.respawn_at:
                pu.active = True
                self.events_queue.append({
                    "type": "powerup_respawned",
                    "id": pu.id,
                    "x": pu.x,
                    "y": pu.y,
                    "power_type": pu.type
                })

        # 4. Update Bullets (Spatial Hash Bouncing & Collision)
        expired_bullets: List[str] = []
        living_players = [p for p in self.players.values() if p.alive and not p.is_spectator]
        hit_radius_sq = (PLAYER_RADIUS + BULLET_RADIUS) ** 2

        for b_id, b in self.bullets.items():
            if now - b.created_at >= b.lifespan or b.bounces_left < 0:
                expired_bullets.append(b_id)
                continue

            sub_steps = 3
            sub_dt = dt / sub_steps
            hit_something = False

            for _ in range(sub_steps):
                dx = b.vx * sub_dt
                dy = b.vy * sub_dt
                
                bounced = self._bounce_bullet_against_walls(b, dx, dy)
                if bounced:
                    b.bounces_left -= 1
                    if b.bounces_left < 0:
                        expired_bullets.append(b_id)
                        hit_something = True
                        break

                bx, by = b.x, b.y
                for p in living_players:
                    d_sq = (bx - p.x) ** 2 + (by - p.y) ** 2
                    if d_sq <= hit_radius_sq:
                        self.kill_player(p, b.owner_id)
                        expired_bullets.append(b_id)
                        hit_something = True
                        break

                if hit_something:
                    break

        for b_id in expired_bullets:
            if b_id in self.bullets:
                del self.bullets[b_id]

    def _apply_powerup(self, player: PlayerState, pu: PowerUpItem):
        pu.active = False
        pu.respawn_at = time.time() + 15.0
        player.active_power = pu.type
        
        if pu.type == PowerUpType.SPEED_BOOST:
            player.speed_boost_timer = 8.0
        elif pu.type == PowerUpType.SHIELD:
            player.shield = True
            player.shield_timer = 8.0
        elif pu.type == PowerUpType.MULTI_BOUNCE:
            player.multi_bounce_timer = 10.0
        elif pu.type == PowerUpType.RAPID_BURST:
            player.rapid_burst_charges = 2
        elif pu.type == PowerUpType.MEGA_BEAM:
            pass

        self.events_queue.append({
            "type": "powerup_collected",
            "player_id": player.id,
            "power_type": pu.type,
            "pu_id": pu.id
        })

    def _check_grid_sync(self):
        walls_id = id(self.map_def.walls)
        if walls_id != getattr(self, '_last_walls_id', None) or len(self.map_def.walls) != self._last_wall_count:
            self.spatial_grid.build(self.map_def.walls)
            self._last_walls_id = walls_id
            self._last_wall_count = len(self.map_def.walls)

    def _move_circle_against_walls(self, player: PlayerState, dx: float, dy: float):
        """Move player with O(1) spatial candidate walls."""
        self._check_grid_sync()
        candidate_walls = self.spatial_grid.get_candidate_walls(player.x, player.y, PLAYER_RADIUS + abs(dx) + abs(dy) + 30.0)
        if not candidate_walls:
            candidate_walls = self.map_def.walls
        
        new_x = player.x + dx
        collided_x = False
        for w in candidate_walls:
            if self._circle_intersects_aabb(new_x, player.y, PLAYER_RADIUS, w.x, w.y, w.w, w.h):
                collided_x = True
                break
        if not collided_x:
            player.x = max(PLAYER_RADIUS, min(self.map_def.width - PLAYER_RADIUS, new_x))

        new_y = player.y + dy
        collided_y = False
        for w in candidate_walls:
            if self._circle_intersects_aabb(player.x, new_y, PLAYER_RADIUS, w.x, w.y, w.w, w.h):
                collided_y = True
                break
        if not collided_y:
            player.y = max(PLAYER_RADIUS, min(self.map_def.height - PLAYER_RADIUS, new_y))

    def _bounce_bullet_against_walls(self, b: BulletState, dx: float, dy: float) -> bool:
        """Move bullet and reflect off spatially indexed walls."""
        self._check_grid_sync()
        next_x = b.x + dx
        next_y = b.y + dy
        candidate_walls = self.spatial_grid.get_candidate_walls(b.x, b.y, BULLET_RADIUS + abs(dx) + abs(dy) + 30.0)
        if not candidate_walls:
            candidate_walls = self.map_def.walls

        for w in candidate_walls:
            if self._circle_intersects_aabb(next_x, next_y, BULLET_RADIUS, w.x, w.y, w.w, w.h):
                cx = max(w.x, min(b.x, w.x + w.w))
                cy = max(w.y, min(b.y, w.y + w.h))
                
                diff_x = b.x - cx
                diff_y = b.y - cy

                if abs(diff_x) > abs(diff_y):
                    b.vx = -b.vx
                    b.x += b.vx * 0.02
                else:
                    b.vy = -b.vy
                    b.y += b.vy * 0.02

                self.events_queue.append({
                    "type": "bullet_bounce",
                    "x": b.x,
                    "y": b.y
                })
                return True

        b.x = next_x
        b.y = next_y
        return False

    @staticmethod
    def _circle_intersects_aabb(cx: float, cy: float, r: float, rx: float, ry: float, rw: float, rh: float) -> bool:
        closest_x = max(rx, min(cx, rx + rw))
        closest_y = max(ry, min(cy, ry + rh))
        dx = cx - closest_x
        dy = cy - closest_y
        return (dx * dx + dy * dy) <= (r * r)

    def get_snapshot(self) -> Dict[str, Any]:
        """High-performance snapshot serialization with dirty-cached leaderboard."""
        if self._leaderboard_dirty:
            self._cached_leaderboard = sorted(
                [
                    {
                        "id": p.id,
                        "name": p.name,
                        "color": p.color,
                        "score": p.score,
                        "kills": p.kills,
                        "deaths": p.deaths,
                        "streak": p.streak,
                        "alive": p.alive,
                        "is_bot": p.is_bot
                    }
                    for p in self.players.values() if not p.is_spectator
                ],
                key=lambda x: (x["alive"], x["kills"], x["score"]),
                reverse=True
            )
            self._leaderboard_dirty = False

        players_data = {
            pid: {
                "id": p.id,
                "name": p.name,
                "color": p.color,
                "x": round(p.x, 1),
                "y": round(p.y, 1),
                "angle": round(p.angle, 3),
                "alive": p.alive,
                "shield": p.shield,
                "speed_boost": p.speed_boost_timer > 0,
                "multi_bounce": p.multi_bounce_timer > 0,
                "beam_charging": p.beam_charge_timer > 0,
                "active_power": p.active_power,
                "score": p.score,
                "kills": p.kills,
                "deaths": p.deaths,
                "streak": p.streak,
                "is_bot": p.is_bot
            }
            for pid, p in self.players.items() if not p.is_spectator
        }

        bullets_data = [
            {
                "id": b.id,
                "x": round(b.x, 1),
                "y": round(b.y, 1),
                "vx": round(b.vx, 1),
                "vy": round(b.vy, 1),
                "bounces": b.bounces_left,
                "color": b.color
            }
            for b in self.bullets.values()
        ]

        powerups_data = [
            {
                "id": pu.id,
                "type": pu.type,
                "x": pu.x,
                "y": pu.y,
                "active": pu.active
            }
            for pu in self.powerups.values()
        ]

        events = self.events_queue
        self.events_queue = []

        return {
            "type": "state_update",
            "room_id": self.room_id,
            "status": self.status,
            "winner": self.winner,
            "players": players_data,
            "bullets": bullets_data,
            "powerups": powerups_data,
            "leaderboard": self._cached_leaderboard,
            "events": events,
            "server_time": time.time()
        }


class GameManager:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self._init_default_rooms()

    def _init_default_rooms(self):
        self.create_room("arena-1", "Arena Clásica LEGO", "ciudad_bloques", max_players=20, bots_enabled=True, target_bots=4)
        self.create_room("arena-2", "Neón Cyber Caos", "laberinto_neon", max_players=20, bots_enabled=True, target_bots=5)
        self.create_room("arena-3", "Encrucijada Toy", "cruces_juguete", max_players=20, bots_enabled=True, target_bots=6)
        self.create_room("arena-4", "Castillo Pastel", "fortaleza_pastel", max_players=20, bots_enabled=True, target_bots=4)
        self.create_room("arena-5", "Coliseo 360", "coliseo_360", max_players=20, bots_enabled=True, target_bots=8)

    def create_room(self, room_id: str, name: str, map_id: str,
                    max_players: int = 20, bots_enabled: bool = True, target_bots: int = 4) -> GameRoom:
        room = GameRoom(
            room_id=room_id,
            name=name,
            map_id=map_id,
            max_players=max_players,
            bots_enabled=bots_enabled,
            target_bots=target_bots
        )
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        return self.rooms.get(room_id)

    def list_rooms(self) -> List[RoomSummary]:
        return [room.get_summary() for room in self.rooms.values()]
