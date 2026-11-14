"""
Integration tests for FastAPI REST APIs, maps, and Prometheus endpoints.
"""
import os
os.environ["EPSINC_TESTING"] = "1"
import unittest
from server.app import health_check, metrics, list_maps, list_rooms, create_room

def run_async(coro):
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value

class TestAPI(unittest.TestCase):
    def test_health_endpoint(self):
        data = run_async(health_check())
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "EpsInc")

    def test_metrics_prometheus(self):
        res = run_async(metrics())
        content = res.body.decode("utf-8")
        self.assertIn("epsinc_connected_players", content)
        self.assertIn("epsinc_active_rooms", content)

    def test_list_5_original_maps(self):
        maps = run_async(list_maps())
        self.assertGreaterEqual(len(maps), 5, "Must provide at least 5 original maps")
        map_ids = [m["id"] for m in maps]
        self.assertIn("ciudad_bloques", map_ids)
        self.assertIn("laberinto_neon", map_ids)
        self.assertIn("cruces_juguete", map_ids)
        self.assertIn("fortaleza_pastel", map_ids)
        self.assertIn("coliseo_360", map_ids)

    def test_room_listing_and_creation(self):
        rooms = run_async(list_rooms())
        self.assertGreaterEqual(len(rooms), 1)

        new_room_payload = {
            "name": "Sala de Torneo",
            "map_id": "coliseo_360",
            "max_players": 16,
            "bots_enabled": True,
            "target_bots": 3
        }
        created_data = run_async(create_room(new_room_payload))
        self.assertEqual(created_data["name"], "Sala de Torneo")
        self.assertEqual(created_data["max_players"], 16)

if __name__ == "__main__":
    unittest.main()
