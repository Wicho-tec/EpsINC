"""
Unit tests for Game Engine, PowerUps, Streaks, Bots, and Win/Loss logic.
"""
import unittest
import time
from server.models import PowerUpType, PowerUpItem
from server.game_engine import GameRoom, GameManager

class TestGameEngine(unittest.TestCase):
    def setUp(self):
        self.room = GameRoom("test-engine", "Engine Test Room", "ciudad_bloques", max_players=20, bots_enabled=False)

    def test_room_player_limit_20(self):
        """Room enforces up to 20 players."""
        self.assertEqual(self.room.max_players, 20)

    def test_spectator_mode(self):
        """Spectator joins without consuming player spawn or being targetable."""
        spectator, token = self.room.add_player("spec_1", "Viewer", is_spectator=True)
        self.assertTrue(spectator.is_spectator)
        self.assertFalse(spectator.alive)
        self.assertIn("spec_1", self.room.spectators)

    def test_powerup_speed_boost(self):
        """Speed boost increases speed timer."""
        player, _ = self.room.add_player("p_speed", "Speedy")
        pu = PowerUpItem(id="pu1", type=PowerUpType.SPEED_BOOST, x=player.x, y=player.y, active=True)
        
        self.room._apply_powerup(player, pu)
        self.assertGreater(player.speed_boost_timer, 0.0)
        self.assertEqual(player.active_power, PowerUpType.SPEED_BOOST)
        self.assertFalse(pu.active)

    def test_powerup_shield_absorbs_hit(self):
        """Shield powerup prevents death on hit and breaks shield."""
        victim, _ = self.room.add_player("p_victim", "Victim")
        killer, _ = self.room.add_player("p_killer", "Killer")

        victim.shield = True
        victim.shield_timer = 5.0
        victim.alive = True

        self.room.kill_player(victim, killer.id)

        self.assertTrue(victim.alive, "Victim should survive hit due to shield")
        self.assertFalse(victim.shield, "Shield should be consumed after hit")

    def test_kill_streak_triggers(self):
        """3, 4, 5 consecutive kills trigger EPSTAKILL streaks."""
        killer, _ = self.room.add_player("p_rambo", "Rambo")
        victim, _ = self.room.add_player("p_dummy", "Dummy")

        # Kill 1
        self.room.kill_player(victim, killer.id)
        self.assertEqual(killer.streak, 1)

        # Kill 2
        victim.alive = True
        self.room.kill_player(victim, killer.id)
        self.assertEqual(killer.streak, 2)

        # Kill 3 -> streak x3
        victim.alive = True
        self.room.kill_player(victim, killer.id)
        self.assertEqual(killer.streak, 3)

        # Check that event was generated
        streak_events = [e for e in self.room.events_queue if e.get("type") == "player_killed" and e.get("streak") == 3]
        self.assertTrue(len(streak_events) > 0)

    def test_match_win_epswin(self):
        """Eliminating opponents leaves last survivor as winner with EPSWIN."""
        p1, _ = self.room.add_player("p1", "Champion")
        p2, _ = self.room.add_player("p2", "Rival")

        self.room.kill_player(p2, p1.id)

        self.assertEqual(p1.score, 1)
        self.assertEqual(self.room.status, "ended")
        self.assertEqual(self.room.winner, "Champion")
        
        win_events = [e for e in self.room.events_queue if e.get("type") == "match_won"]
        self.assertTrue(len(win_events) > 0)

    def test_bot_synchronization(self):
        """Bots fill room up to target_bots count when enabled."""
        bot_room = GameRoom("bot-room", "Bot Arena", "laberinto_neon", max_players=20, bots_enabled=True, target_bots=4)
        bot_room._sync_bots()

        bot_count = sum(1 for p in bot_room.players.values() if p.is_bot)
        self.assertEqual(bot_count, 4)

if __name__ == "__main__":
    unittest.main()
