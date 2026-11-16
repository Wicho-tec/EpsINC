"""Summarize preserved Locust CSV and Prometheus measurements without inventing capacity."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "resultados"


def analyze():
    samples = [json.loads(line) for line in (ROOT / "prometheus.jsonl").read_text(encoding="utf-8").splitlines() if line]
    results = {}
    for profile in ("rampa-final", "pico", "espectadores"):
        with (ROOT / f"{profile}_stats.csv").open(encoding="utf-8-sig", newline="") as stream:
            stats = {row["Name"]: row for row in csv.DictReader(stream)}
        with (ROOT / f"{profile}_stats_history.csv").open(encoding="utf-8-sig", newline="") as stream:
            history = list(csv.DictReader(stream))
        assert stats and history, f"Missing data for {profile}"
        aggregate = stats["Aggregated"]
        duration = float(aggregate["Request Count"]) / float(aggregate["Requests/s"])
        end = max(float(row["Timestamp"]) for row in history)
        start = end - duration
        ccu_key = "spectator_ccu" if profile == "espectadores" else "human_ccu"
        relevant = []
        for sample in samples:
            values = sample.get(ccu_key, [])
            if isinstance(values, list) and values and start <= values[0]["value"][0] <= end:
                relevant.append(sample)
        ccu = [float(row[ccu_key][0]["value"][1]) for row in relevant]
        ticks = [float(value["value"][1]) for row in relevant for value in row.get("tick_p99_ms", [])]
        ticks = [value for value in ticks if math.isfinite(value)]
        connect = stats["Spectator_Connect" if profile == "espectadores" else "Player_Connect"]
        disconnect = stats.get("Player_Disconnected", {})
        result = {
            "start_epoch": start, "end_epoch": end, "duration_seconds": duration,
            "virtual_users_peak": max(int(row["User Count"]) for row in history),
            "connections_attempted": int(connect["Request Count"]),
            "connection_failures": int(connect["Failure Count"]),
            "disconnect_events": int(disconnect.get("Request Count", 0)),
            "total_events": int(aggregate["Request Count"]),
            "failed_events": int(aggregate["Failure Count"]),
            "observed_ccu_peak": max(ccu) if ccu else None,
            "observed_ccu_last": ccu[-1] if ccu else None,
            "observed_ccu_average": sum(ccu) / len(ccu) if ccu else None,
            "tick_p99_peak_ms": max(ticks) if ticks else None,
            "metrics_samples": len(relevant),
        }
        if "Player_Ping_RTT" in stats:
            result["answered_ping_p99_ms"] = float(stats["Player_Ping_RTT"]["99%"])
        else:
            receive = stats["Spectator_Receive_Snapshot"]
            attempts = int(receive["Request Count"])
            successful = attempts - int(receive["Failure Count"])
            assert successful > 0, "No successful spectator snapshots"
            result.update(snapshot_mean_bytes=float(receive["Average Content Size"]) * attempts / successful,
                          snapshots_received=successful,
                          receive_failures=int(receive["Failure Count"]),
                          snapshot_receive_p99_ms=float(receive["99%"]),
                          average_snapshots_per_second=float(receive["Requests/s"]))
        results[profile] = result
    size = results["espectadores"]["snapshot_mean_bytes"]
    projected_bytes_per_second = size * 30 * 20000
    results["extrapolation"] = {
        "spectators": 20000, "measured_mean_snapshot_bytes": size, "assumed_broadcast_hz": 30,
        "projected_MB_per_second": projected_bytes_per_second / 1e6,
        "projected_Gbps": projected_bytes_per_second * 8 / 1e9,
        "projected_GiB_per_hour": projected_bytes_per_second * 3600 / 1024**3,
        "gross_egress_USD_per_hour_at_0_09_per_GiB": projected_bytes_per_second * 3600 / 1024**3 * 0.09,
        "node_count": "Not validated; no linear node-capacity claim",
        "basis": "Measured snapshot size; assumed 30 Hz; not a 20,000-user test",
    }
    assert projected_bytes_per_second >= 0
    (ROOT / "analysis.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    analyze()
