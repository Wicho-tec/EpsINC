"""
Unit tests for projectile physics, wall bouncing, and collision detection.
"""
import unittest
import time
from server.models import BulletState, WallRect, PlayerState
from server.game_engine import GameRoom

class TestPhysics(unittest.TestCase):
    def setUp(self):
        self.room = GameRoom("test-physics", "Physics Room", "ciudad_bloques", bots_enabled=False)

    def test_bullet_bounces_vertical_wall(self):
        """A bullet flying horizontally into a vertical wall reflects vx."""
        # Create a vertical wall at x=100..140, y=0..300
        wall = WallRect(x=100, y=0, w=40, h=300)
        self.room.map_def.walls = [wall]

        bullet = BulletState(
            id="b1",
            owner_id="p1",
            x=80.0,
            y=150.0,
            vx=300.0,
            vy=0.0,
            bounces_left=4,
            max_bounces=4,
            created_at=time.time()
        )
        self.room.bullets[bullet.id] = bullet

        # Update step with dt that hits the wall
        bounced = self.room._bounce_bullet_against_walls(bullet, dx=30.0, dy=0.0)
        self.assertTrue(bounced)
        self.assertLess(bullet.vx, 0, "Bullet vx should invert on vertical collision")

    def test_bullet_bounces_horizontal_wall(self):
        """A bullet flying vertically into a horizontal wall reflects vy."""
        wall = WallRect(x=0, y=100, w=400, h=40)
        self.room.map_def.walls = [wall]

        bullet = BulletState(
            id="b2",
            owner_id="p1",
            x=200.0,
            y=80.0,
            vx=0.0,
            vy=300.0,
            bounces_left=4,
            max_bounces=4,
            created_at=time.time()
        )
        self.room.bullets[bullet.id] = bullet

        bounced = self.room._bounce_bullet_against_walls(bullet, dx=0.0, dy=30.0)
        self.assertTrue(bounced)
        self.assertLess(bullet.vy, 0, "Bullet vy should invert on horizontal collision")

    def test_bullet_expires_after_5_seconds(self):
        """Bullets must expire and be deleted after 5 seconds lifespan."""
        now = time.time()
        old_bullet = BulletState(
            id="b_old",
            owner_id="p1",
            x=500.0,
            y=500.0,
            vx=100.0,
            vy=0.0,
            bounces_left=4,
            max_bounces=4,
            created_at=now - 5.1, # 5.1 seconds ago
            lifespan=5.0
        )
        self.room.bullets[old_bullet.id] = old_bullet
        self.room.update(dt=0.033)

        self.assertNotIn("b_old", self.room.bullets, "Expired bullet should be removed")

    def test_bullet_can_kill_shooter_suicide(self):
        """Projectiles can bounce and eliminate the player who shot them (like TankTrouble)."""
        player, _ = self.room.add_player("p_shooter", "Shooter")
        player.x = 300.0
        player.y = 300.0
        player.alive = True
        player.score = 5

        # Place a bullet directly on top of the shooter
        bullet = BulletState(
            id="b_suicide",
            owner_id="p_shooter",
            x=300.0,
            y=300.0,
            vx=0.0,
            vy=0.0,
            bounces_left=2,
            max_bounces=4,
            created_at=time.time()
        )
        self.room.bullets[bullet.id] = bullet

        self.room.update(dt=0.033)

        self.assertFalse(player.alive, "Player should be eliminated by own bullet")
        self.assertEqual(player.deaths, 1)
        self.assertEqual(player.streak, 0, "Streak resets to 0 on self-elimination")

    def test_player_wall_sliding_collision(self):
        """Player cannot pass through LEGO walls."""
        wall = WallRect(x=200, y=100, w=50, h=400)
        self.room.map_def.walls = [wall]

        player, _ = self.room.add_player("p_mover", "Mover")
        player.x = 170.0 # radius is 24, so right edge is at 194
        player.y = 200.0

        # Attempt to move directly right through the wall
        self.room._move_circle_against_walls(player, dx=20.0, dy=0.0)

        # Player should have been stopped before entering the wall
        self.assertLess(player.x, 200.0, "Player should be blocked by wall")

if __name__ == "__main__":
    unittest.main()
