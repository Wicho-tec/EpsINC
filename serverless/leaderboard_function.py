"""Persistent leaderboard for the EpsINC classroom deployment."""
import base64
import json
import os
import re
import time
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

_TABLE = None


def get_table():
    global _TABLE
    if _TABLE is None:
        _TABLE = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _TABLE


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", event.get("httpMethod", "GET"))
    path = event.get("rawPath", event.get("path", "/leaderboard/top"))
    headers = {"Content-Type": "application/json"}

    def response(status, body):
        return {"statusCode": status, "headers": headers,
                "body": json.dumps(body, default=lambda value: int(value) if isinstance(value, Decimal) else str(value))}

    try:
        if method == "GET" and path == "/leaderboard/top":
            limit = int((event.get("queryStringParameters") or {}).get("limit", 25))
            if not 1 <= limit <= 100:
                raise ValueError("limit must be between 1 and 100")
            # shortcut: query/sort suits a small classroom board; add a score index for large boards.
            result = get_table().query(KeyConditionExpression=Key("board").eq("main"), ConsistentRead=True)
            if result.get("LastEvaluatedKey"):
                return response(503, {"error": "Board exceeds demo query capacity"})
            items = sorted(result["Items"], key=lambda item: (item["score"], item["kills"]), reverse=True)
            return response(200, {"leaderboard": items[:limit], "total_tracked": len(items), "generated_at": int(time.time())})
        if method == "POST" and path == "/leaderboard/submit":
            raw = event.get("body") or "{}"
            if event.get("isBase64Encoded"):
                raw = base64.b64decode(raw).decode("utf-8")
            body = json.loads(raw)
            if not isinstance(body, dict):
                raise ValueError("Expected JSON object")
            player_id = body.get("player_id", "")
            name = body.get("name", "")
            if not isinstance(player_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", player_id):
                raise ValueError("Invalid player_id")
            if not isinstance(name, str) or not 1 <= len(name) <= 20:
                raise ValueError("name must contain 1 to 20 characters")
            values = {key: body.get(key, 0) for key in ("score", "kills", "streak")}
            if any(type(value) is not int or not 0 <= value <= 1000000 for value in values.values()):
                raise ValueError("Scores must be integers between 0 and 1000000")
            item = {"board": "main", "player_id": player_id, "name": name,
                    **values, "updated_at": int(time.time())}
            # Replacing a submitted total makes retries idempotent.
            get_table().put_item(Item=item)
            return response(200, {"status": "success", "player": item})
        return response(404, {"error": "Route not found"})
    except (ValueError, TypeError, UnicodeError) as error:
        return response(400, {"error": str(error)})
    except ClientError:
        return response(503, {"error": "Leaderboard storage unavailable"})
