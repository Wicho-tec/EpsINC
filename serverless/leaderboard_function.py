"""
EpsInc - Serverless Leaderboard Function
Handles high-concurrency score submission, ranking retrieval, and caching via serverless compute.
"""
import json
import time
import os
from typing import Dict, Any, List

# In-memory mock/fallback storage for serverless runtime (can integrate Redis/DynamoDB/Firestore)
_MEMORY_STORE: Dict[str, Dict[str, Any]] = {
    "p_demo_1": {"name": "TerminatorBaby", "score": 1420, "kills": 284, "streak_record": 12, "updated_at": 1700000000},
    "p_demo_2": {"name": "LegoSniper", "score": 1180, "kills": 236, "streak_record": 9, "updated_at": 1700000100},
    "p_demo_3": {"name": "ChuponFeroz", "score": 950, "kills": 190, "streak_record": 8, "updated_at": 1700000200},
}

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda / Cloud Function entrypoint."""
    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "/leaderboard")
    
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    if http_method == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "ok"})}

    # GET /leaderboard/top
    if http_method == "GET" and "/top" in path:
        limit = int(event.get("queryStringParameters", {}).get("limit", 25)) if event.get("queryStringParameters") else 25
        sorted_players = sorted(
            [{"id": pid, **data} for pid, data in _MEMORY_STORE.items()],
            key=lambda x: (x["score"], x["kills"]),
            reverse=True
        )[:limit]

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "leaderboard": sorted_players,
                "total_tracked": len(_MEMORY_STORE),
                "generated_at": time.time()
            })
        }

    # POST /leaderboard/submit
    if http_method == "POST" and "/submit" in path:
        try:
            body = json.loads(event.get("body", "{}"))
            player_id = body.get("player_id", f"p_{int(time.time())}")
            name = body.get("name", "BiberonAnónimo")[:20]
            score_delta = int(body.get("score", 0))
            kills_delta = int(body.get("kills", 0))
            streak = int(body.get("streak", 0))

            if player_id in _MEMORY_STORE:
                _MEMORY_STORE[player_id]["score"] += score_delta
                _MEMORY_STORE[player_id]["kills"] += kills_delta
                _MEMORY_STORE[player_id]["streak_record"] = max(_MEMORY_STORE[player_id]["streak_record"], streak)
                _MEMORY_STORE[player_id]["updated_at"] = time.time()
            else:
                _MEMORY_STORE[player_id] = {
                    "name": name,
                    "score": score_delta,
                    "kills": kills_delta,
                    "streak_record": streak,
                    "updated_at": time.time()
                }

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"status": "success", "player": _MEMORY_STORE[player_id]})
            }
        except Exception as e:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": str(e)})}

    return {
        "statusCode": 404,
        "headers": headers,
        "body": json.dumps({"message": "Ruta de tabla de líderes no encontrada"})
    }
