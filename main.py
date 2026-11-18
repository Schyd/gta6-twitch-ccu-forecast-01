"""gta6-twitch-ccu-forecast-01 entry in Python 3.13 (standard library only).

Forecasts Twitch concurrent viewers in the Grand Theft Auto VI category for
hours 2..24 of release day 2026-11-19 (UTC), as five quantiles per hour,
from the case's hour-1 print and the launch-day shapes of past big launches.

Method
------
For every comparable launch in the case, take the log ratio of each hour's
viewers to that launch's hour-1 viewers, ln(v_h / v_1). For hour h, the
forecast quantiles are hour 1's print times exp() of the empirical quantiles
of those log ratios across all comparables that have both hours:

    q_tau(h) = p1 * exp(quantile_tau({ln(v_h / v_1)}))

Rolling midnight-local unlocks (New Zealand first, then Europe, the UK, the
US East at 05:00Z and West at 08:00Z) make viewership rise through the
morning and fall late; the cross-launch distribution captures that shape
and its honest spread, instead of assuming every hour stays at hour 1.

Guards: a comparable is used only when its hour-1 print is at least 10,000
viewers (small, sparsely sampled categories and single-global-unlock games
whose hour 1 is nearly empty have exploding ratios that do not describe a
rolling midnight-local console launch, and the target's own pre-release
history is not a launch); an hour with fewer than 5 ratios falls back to
the house baseline's persistence spread. The empirical quantiles are
blended 75/25 in log space with the baseline's persistence quantiles, so
an atypical final shape cannot pull the forecast far from a sane prior.
Everything is deterministic: no randomness, no network, no clock reads.

Run locally:
    mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first, so a module
# shipped beside this file imports.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]  # standard normal quantiles
SIGMA = 0.15  # house baseline spread, log units per sqrt hour
MIN_HOUR1 = 10000  # ignore tiny / pre-release histories as shape donors
MIN_RATIOS = 5    # else fall back to the persistence spread
BLEND_W = 0.75    # weight of the empirical quantiles vs the baseline prior


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def round2(x):
    """Round to 2 decimals, half up (as the house baseline does)."""
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if float(value).is_integer() else value


def empirical_quantile(sorted_values, tau):
    """Linear-interpolation quantile of an ascending list."""
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    pos = tau * (n - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def log_ratios_by_hour(case):
    """{hour: [ln(v_h / v_1), ...]} over the case's comparable launches."""
    ratios = {h: [] for h in range(2, 25)}
    for comp in case.get("comparables") or []:
        try:
            day_start = parse_time(comp["day_start"])
        except (KeyError, ValueError):
            continue
        by_hour = {}
        for pt in comp.get("hourly") or []:
            try:
                v = pt["viewers"]
                h = int((parse_time(pt["from"]) - day_start).total_seconds() // 3600) + 1
            except (KeyError, ValueError, TypeError):
                continue
            if 1 <= h <= 24 and v and v > 0:
                by_hour[h] = v
        v1 = by_hour.get(1)
        if not v1 or v1 < MIN_HOUR1:
            continue
        for h in range(2, 25):
            if h in by_hour:
                ratios[h].append(math.log(by_hour[h] / v1))
    return ratios


def forecast_case(case, name):
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    if first is None:
        raise ValueError(f"{name} has no hour-1 print")
    p1 = max(1, first["viewers"])
    ratios = log_ratios_by_hour(case)
    hours = []
    for row in case["forecast"]:
        h = row["hour"]
        vals = sorted(ratios[h])
        if len(vals) >= MIN_RATIOS:
            qs = [p1 * math.exp(empirical_quantile(vals, tau)) for tau in LEVELS]
        else:
            qs = [p1 * math.exp(z * SIGMA * math.sqrt(h - 1)) for z in Z]
        # Blend with the persistence prior in log space (robustness).
        prior = [p1 * math.exp(z * SIGMA * math.sqrt(h - 1)) for z in Z]
        qs = [math.exp(BLEND_W * math.log(q) + (1 - BLEND_W) * math.log(p))
              for q, p in zip(qs, prior)]
        qs = [round2(min(max(q, 0.01), 1e9)) for q in qs]
        for i in range(1, 5):  # keep quantiles non-decreasing after rounding
            if qs[i] < qs[i - 1]:
                qs[i] = qs[i - 1]
        hours.append({"hour": h, "q": qs})
    return {"hours": hours}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
