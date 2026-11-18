"""Local validation for main.py (NOT part of the entry; dev only).

Leave-one-out over the comparables with complete release-day data: for each
held-out launch, forecast its hours 2..24 from its hour-1 print and the
other launches' shapes, then score mean pinball loss on the log scale
against its actual hours, exactly as the contest scores. Compares:
  A) main.py's empirical-ratio model
  B) the house baseline (persistence, sigma 0.15)
  C) a 50/50 log-space blend of A and B
Also scores the four practice cases if answers are supplied (see below).
"""
import json
import math
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import main as M

KIT = Path("/tmp/kits/gta6-twitch-ccu-forecast-01-kit/input")

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]


def pinball_loss(forecast_hours, actual):
    """Mean pinball loss on log scale over hours x quantiles."""
    total, n = 0.0, 0
    for row in forecast_hours:
        y = max(1, actual[row["hour"]])
        for tau, q in zip(LEVELS, row["q"]):
            d = math.log(y) - math.log(max(q, 1e-9))
            total += 2 * max(tau * d, (tau - 1) * d)
            n += 1
    return total / n


def baseline_forecast(p1):
    return {"hours": [
        {"hour": h, "q": [M.round2(p1 * math.exp(z * 0.15 * math.sqrt(h - 1))) for z in Z]}
        for h in range(2, 25)]}


def blend(a, b, w=0.5):
    hours = []
    for ra, rb in zip(a["hours"], b["hours"]):
        qs = [math.exp(w * math.log(qa) + (1 - w) * math.log(qb))
              for qa, qb in zip(ra["q"], rb["q"])]
        qs = [M.round2(q) for q in qs]
        hours.append({"hour": ra["hour"], "q": qs})
    return {"hours": hours}


def launch_day_hours(comp):
    ds = datetime.fromisoformat(comp["day_start"].replace("Z", "+00:00"))
    by_hour = {}
    for pt in comp["hourly"]:
        h = int((datetime.fromisoformat(pt["from"].replace("Z", "+00:00")) - ds)
                .total_seconds() // 3600) + 1
        if 1 <= h <= 24 and pt["viewers"] and pt["viewers"] > 0:
            by_hour[h] = pt["viewers"]
    return by_hour


def main():
    cases = [json.load(open(KIT / f"p0{i}.in")) for i in range(4)]
    comps = cases[0]["comparables"]
    complete = []
    for comp in comps:
        by_hour = launch_day_hours(comp)
        if all(h in by_hour for h in range(1, 25)):
            complete.append((comp["name"], by_hour))
    print(f"complete launches for LOO: {len(complete)}")

    losses = {"A_empirical": [], "B_baseline": [], "C_blend": []}
    for name, by_hour in complete:
        others = [c for c in comps if c["name"] != name]
        pseudo = {"levels": LEVELS,
                  "known": [{"hour": 1, "viewers": by_hour[1]}],
                  "forecast": [{"hour": h} for h in range(2, 25)],
                  "comparables": others}
        fa = M.forecast_case(pseudo, name)
        fb = baseline_forecast(by_hour[1])
        fc = blend(fa, fb)
        for key, f in (("A_empirical", fa), ("B_baseline", fb), ("C_blend", fc)):
            losses[key].append(pinball_loss(f["hours"], by_hour))
    for key, ls in losses.items():
        print(f"{key}: mean pinball loss {sum(ls)/len(ls):.4f} "
              f"(median {sorted(ls)[len(ls)//2]:.4f}, n={len(ls)})")

    # Practice cases: run main.py's forecaster on each (format check only;
    # answers live on SullyGnome, not in the kit).
    for i, case in enumerate(cases):
        f = M.forecast_case(case, f"p0{i}")
        assert len(f["hours"]) == 23 and all(len(r["q"]) == 5 for r in f["hours"])
        print(f"p0{i} {case['game']['name']}: p1={case['known'][0]['viewers']:,} "
              f"h2 median={f['hours'][0]['q'][2]:,} h12 median={f['hours'][10]['q'][2]:,} "
              f"h24 median={f['hours'][22]['q'][2]:,}")


if __name__ == "__main__":
    main()
