"""Phase 1c: destinations and net_switching, derived from lifecycle.parquet
and wins.parquet. Currently produces empty (correctly-shaped) tables because
lifecycle/wins are empty until enough months of history exist -- see
02_lifecycle.py. Re-run once the full data lands; no changes needed here.
"""
import pandas as pd

from common import load_config, path
from privacy import assert_exportable, enforce_k_min


def main():
    cfg = load_config()
    k_min = cfg["privacy"]["k_min"]

    lifecycle = pd.read_parquet(path("data/work/lifecycle.parquet"))
    wins = pd.read_parquet(path("data/work/wins.parquet"))

    # destinations(period, bucket, destination, share, n_cards)
    stayers = lifecycle[lifecycle.status == "stayer"]
    total_stayers = len(stayers)
    if total_stayers:
        destinations = (
            stayers.groupby(["bucket", "destination_chain"])
            .size().rename("n_cards").reset_index()
            .rename(columns={"destination_chain": "destination"})
        )
        destinations["share"] = destinations.n_cards / total_stayers
    else:
        destinations = pd.DataFrame(columns=["bucket", "destination", "n_cards", "share"])
    destinations.insert(0, "period", "current")

    # net_switching(period, competitor, lost_to, won_from, net, n_cards)
    lost_to = stayers[stayers.bucket == "switched"].groupby("destination_chain").size().rename("lost_to")
    won_from = wins.groupby("source_chain").size().rename("won_from") if not wins.empty else pd.Series(dtype=int, name="won_from")
    competitors = sorted(set(lost_to.index) | set(won_from.index))
    net_switching = pd.DataFrame({
        "competitor": competitors,
        "lost_to": [int(lost_to.get(c, 0)) for c in competitors],
        "won_from": [int(won_from.get(c, 0)) for c in competitors],
    })
    if not net_switching.empty:
        net_switching["net"] = net_switching.won_from - net_switching.lost_to
        net_switching["n_cards"] = net_switching.lost_to + net_switching.won_from
    else:
        net_switching = pd.DataFrame(columns=["competitor", "lost_to", "won_from", "net", "n_cards"])
    net_switching.insert(0, "period", "current")

    destinations = enforce_k_min(destinations, k_min)
    net_switching = enforce_k_min(net_switching, k_min)
    assert_exportable(destinations, "destinations")
    assert_exportable(net_switching, "net_switching")

    out_dir = path("data/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    destinations.to_parquet(out_dir / "destinations.parquet", index=False)
    net_switching.to_parquet(out_dir / "net_switching.parquet", index=False)
    print(f"destinations: {len(destinations)} rows (from {total_stayers} stayers)")
    print(f"net_switching: {len(net_switching)} rows")


if __name__ == "__main__":
    main()
