import json
import unittest
from unittest.mock import Mock, patch

from serverless.leaderboard_function import handler


class LeaderboardTests(unittest.TestCase):
    def test_submit_validates_before_writing(self):
        event = {"httpMethod": "POST", "path": "/leaderboard/submit",
                 "body": json.dumps({"player_id": "demo", "name": "Demo", "score": -1})}
        with patch("serverless.leaderboard_function.get_table") as table:
            self.assertEqual(handler(event, None)["statusCode"], 400)
            table.assert_not_called()
            event["body"] = json.dumps({"player_id": "demo", "name": "Demo", "score": 20})
            self.assertEqual(handler(event, None)["statusCode"], 200)
            self.assertEqual(table.return_value.put_item.call_args.kwargs["Item"]["score"], 20)

    def test_top_sorts_and_limits_persisted_scores(self):
        table = Mock()
        table.query.return_value = {"Items": [
            {"score": 5, "kills": 1}, {"score": 10, "kills": 2}]}
        with patch("serverless.leaderboard_function.get_table", return_value=table):
            result = handler({"rawPath": "/leaderboard/top", "queryStringParameters": {"limit": "1"}}, None)
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["leaderboard"], [{"score": 10, "kills": 2}])


if __name__ == "__main__":
    unittest.main()
