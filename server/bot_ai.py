"""
EpsInc - Bot AI Module
Simulates autonomous baby-bottle bots with navigation, aiming, obstacle avoidance, and shooting.
"""
import math
import random
import time
from typing import List, Optional, Tuple, Dict
from server.models import PlayerState, WallRect, PowerUpItem

class BotAI:
    def __init__(self, bot_id: str, name: str, color: str):
        self.bot_id = bot_id
        self.name = name
        self.color = color
        self.target_player_id: Optional[str] = None
        self.shoot_timer = random.uniform(1.0, 2.5)
        self.move_change_timer = random.uniform(0.5, 1.5)
        self.current_direction: Tuple[float, float] = (0.0, 0.0)
        self.wander_angle = random.uniform(0, 2 * math.pi)

    def update(self, dt: float, bot_player: PlayerState, all_players: Dict[str, PlayerState],
               walls: List[WallRect], powerups: List[PowerUpItem], map_w: int, map_h: int) -> Tuple[float, float, float, bool]:
        """
        Updates bot decisions.
        Returns: (move_x, move_y, aim_angle, shoot_trigger)
        """
        if not bot_player.alive:
            return (0.0, 0.0, 0.0, False)

        # 1. Target selection: find closest living enemy player or nearby active powerup
        closest_enemy: Optional[PlayerState] = None
        min_dist_sq = float("inf")
        
        for pid, p in all_players.items():
            if pid == self.bot_id or not p.alive or p.is_spectator:
                continue
            dx = p.x - bot_player.x
            dy = p.y - bot_player.y
            dist_sq = dx * dx + dy * dy
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_enemy = p

        # 2. Movement logic
        self.move_change_timer -= dt
        move_x, move_y = self.current_direction

        if closest_enemy:
            # Aim nipple directly at enemy
            aim_angle = math.atan2(closest_enemy.y - bot_player.y, closest_enemy.x - bot_player.x)
            
            # Distance logic
            dist = math.sqrt(min_dist_sq)
            if self.move_change_timer <= 0:
                self.move_change_timer = random.uniform(0.6, 1.4)
                if dist > 350:
                    # Move closer
                    dx = closest_enemy.x - bot_player.x
                    dy = closest_enemy.y - bot_player.y
                    norm = max(1.0, math.sqrt(dx * dx + dy * dy))
                    # Add slight lateral jitter to avoid being an easy target
                    jitter = random.uniform(-0.4, 0.4)
                    move_x = (dx / norm) + jitter * (-dy / norm)
                    move_y = (dy / norm) + jitter * (dx / norm)
                elif dist < 150:
                    # Too close, back away or circle
                    dx = bot_player.x - closest_enemy.x
                    dy = bot_player.y - closest_enemy.y
                    norm = max(1.0, math.sqrt(dx * dx + dy * dy))
                    move_x = dx / norm
                    move_y = dy / norm
                else:
                    # Circle around target
                    dx = closest_enemy.x - bot_player.x
                    dy = closest_enemy.y - bot_player.y
                    norm = max(1.0, math.sqrt(dx * dx + dy * dy))
                    direction_sign = 1 if random.random() > 0.5 else -1
                    move_x = direction_sign * (-dy / norm)
                    move_y = direction_sign * (dx / norm)
                
                # Normalize
                m_norm = math.sqrt(move_x * move_x + move_y * move_y)
                if m_norm > 0:
                    move_x /= m_norm
                    move_y /= m_norm
                self.current_direction = (move_x, move_y)
        else:
            # Wander around map
            if self.move_change_timer <= 0:
                self.move_change_timer = random.uniform(1.0, 2.5)
                self.wander_angle += random.uniform(-1.0, 1.0)
                move_x = math.cos(self.wander_angle)
                move_y = math.sin(self.wander_angle)
                self.current_direction = (move_x, move_y)
            aim_angle = self.wander_angle

        # 3. Shooting logic
        self.shoot_timer -= dt
        shoot_trigger = False
        if closest_enemy and self.shoot_timer <= 0:
            # Check if wall directly obstructs line of sight
            has_los = self._has_line_of_sight(bot_player.x, bot_player.y, closest_enemy.x, closest_enemy.y, walls)
            if has_los:
                shoot_trigger = True
                self.shoot_timer = random.uniform(0.7, 1.8)
            else:
                # Bounce shot opportunity!
                shoot_trigger = random.random() < 0.35
                self.shoot_timer = random.uniform(0.9, 2.2)

        return (move_x, move_y, aim_angle, shoot_trigger)

    def _has_line_of_sight(self, x1: float, y1: float, x2: float, y2: float, walls: List[WallRect]) -> bool:
        """Fast line-box intersection check with AABB bounding rejection."""
        min_lx = min(x1, x2)
        max_lx = max(x1, x2)
        min_ly = min(y1, y2)
        max_ly = max(y1, y2)

        for w in walls:
            # Quick bounding box rejection
            if min_lx > w.x + w.w or max_lx < w.x or min_ly > w.y + w.h or max_ly < w.y:
                continue
            if self._line_intersects_rect(x1, y1, x2, y2, w.x, w.y, w.w, w.h):
                return False
        return True

    def _line_intersects_rect(self, x1: float, y1: float, x2: float, y2: float, rx: float, ry: float, rw: float, rh: float) -> bool:
        # Check if line segment intersects any of the 4 borders of rect
        rect_lines = [
            (rx, ry, rx + rw, ry),
            (rx + rw, ry, rx + rw, ry + rh),
            (rx + rw, ry + rh, rx, ry + rh),
            (rx, ry + rh, rx, ry)
        ]
        for lx1, ly1, lx2, ly2 in rect_lines:
            if self._segments_intersect(x1, y1, x2, y2, lx1, ly1, lx2, ly2):
                return True
        return False

    def _segments_intersect(self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float) -> bool:
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        A, B, C, D = (x1, y1), (x2, y2), (x3, y3), (x4, y4)
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
