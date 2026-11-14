"""Extrapolate spectator bandwidth and indicative AWS infrastructure cost."""
import math
from typing import Any, Dict

NODE_HOURLY_USD = 0.1008  # m7i.large, us-east-1, Linux On-Demand estimate
EKS_HOURLY_USD = 0.10     # EKS standard-support cluster fee
EGRESS_USD_PER_GB = 0.09  # gross internet egress estimate; free tier excluded
CONNECTIONS_PER_NODE = 3500  # unmeasured planning assumption


def calculate_spectator_demands(
    spectator_count: int,
    snapshot_size_kb: float = 1.25,
    broadcast_hz: int = 30,
) -> Dict[str, Any]:
    if spectator_count < 1 or snapshot_size_kb <= 0 or broadcast_hz < 1:
        raise ValueError("spectators, snapshot size, and broadcast rate must be positive")

    bandwidth_mb_s = snapshot_size_kb * broadcast_hz * spectator_count / 1024
    gb_per_hour = bandwidth_mb_s * 3600 / 1024
    nodes_required = math.ceil(spectator_count / CONNECTIONS_PER_NODE)
    compute_cost = nodes_required * NODE_HOURLY_USD + EKS_HOURLY_USD
    egress_cost = gb_per_hour * EGRESS_USD_PER_GB
    total_cost = compute_cost + egress_cost

    return {
        "spectators": spectator_count,
        "snapshot_size_kb": snapshot_size_kb,
        "broadcast_hz": broadcast_hz,
        "bandwidth_mb_s": round(bandwidth_mb_s, 2),
        "bandwidth_gbps": round(bandwidth_mb_s * 8 / 1024, 2),
        "memory_mb": round(spectator_count * 44 / 1024, 2),
        "nodes_required": nodes_required,
        "egress_gb_hour": round(gb_per_hour, 2),
        "egress_cost_hour_usd": round(egress_cost, 2),
        "compute_cost_hour_usd": round(compute_cost, 4),
        "total_cost_hour_usd": round(total_cost, 2),
        "cost_per_spectator_hour_usd": round(total_cost / spectator_count, 5),
    }


def print_extrapolation_report():
    print("EpsInc — extrapolación matemática; no representa una prueba de carga")
    print("Supuestos: 1.25 KB/snapshot, 30 Hz, 44 KB/socket y 3,500 conexiones/nodo")
    print("El límite por nodo no está medido. Costos brutos; egreso gratis mensual excluido.")
    print(f"{'Espectadores':>13} {'MB/s':>10} {'Gbps':>8} {'RAM MB':>10} "
          f"{'Nodos':>7} {'USD/h':>10} {'USD/espectador-h':>18}")
    for count in (100, 500, 1000, 5000, 10000, 20000):
        row = calculate_spectator_demands(count)
        print(f"{count:>13} {row['bandwidth_mb_s']:>10.2f} {row['bandwidth_gbps']:>8.2f} "
              f"{row['memory_mb']:>10.2f} {row['nodes_required']:>7} "
              f"{row['total_cost_hour_usd']:>10.2f} "
              f"{row['cost_per_spectator_hour_usd']:>18.5f}")


if __name__ == "__main__":
    assert calculate_spectator_demands(20000)["nodes_required"] == 6
    assert calculate_spectator_demands(20000)["bandwidth_gbps"] == 5.72
    print_extrapolation_report()
