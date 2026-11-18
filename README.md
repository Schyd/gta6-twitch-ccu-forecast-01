# gta6-twitch-ccu-forecast-01

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/schyd/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/schyd/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Forecasts Twitch concurrent viewers in the Grand Theft Auto VI category for
hours 2–24 of release day 2026-11-19 (UTC), as five quantiles per hour.
Method: for each comparable past launch, the log ratio of each hour's
viewers to its hour-1 print; the forecast quantiles are hour 1's print
times exp() of the empirical quantiles of those ratios across launches
with hour-1 prints of at least 10,000, blended 75/25 in log space with the
house baseline's persistence spread. Standard library only, deterministic,
no network.

Local validation (`validate_local.py`, leave-one-out over the 37
comparables with complete release-day data): mean pinball loss 0.28 on
launches with hour-1 prints above 20,000, against the house baseline's
~0.39 on the practice cases.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
